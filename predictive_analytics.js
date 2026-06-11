/**
 * PS VIBE Predictive Analytics Engine
 * Express API server that queries MySQL for:
 * - Sales trends
 * - Peak hours prediction
 * - Popular games ranking
 * - Member growth tracking
 * - Revenue forecasting
 * Port: 3120
 */
const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// ─── MySQL Connection ───
const DB_CONFIG = {
  host: '127.0.0.1',
  port: 3306,
  user: 'psvibe_user',
  password: 'PsVibe@2026_Rotated!',
  database: 'psvibe_api',
  charset: 'utf8mb4'
};

let pool = null;

async function getPool() {
  if (!pool) {
    pool = mysql.createPool(DB_CONFIG);
  }
  return pool;
}

async function query(sql, params = []) {
  const p = await getPool();
  const [rows] = await p.query(sql, params);
  return rows;
}

// ─── Endpoints ───

/** GET /health — Health check */
app.get('/health', async (_req, res) => {
  try {
    const p = await getPool();
    await p.query('SELECT 1');
    res.json({ status: 'ok', service: 'predictive-analytics', mysql: 'connected' });
  } catch (e) {
    res.status(503).json({ status: 'error', service: 'predictive-analytics', error: e.message });
  }
});

/** GET /analytics/sales-trend — 30-day sales chart data */
app.get('/analytics/sales-trend', async (req, res) => {
  try {
    const rows = await query(`
      SELECT DATE(sale_date) as day,
             COALESCE(SUM(amount), 0) as total,
             COUNT(*) as count
      FROM sales_daily
      WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
      GROUP BY DATE(sale_date)
      ORDER BY day ASC
    `);
    const data = rows.map(r => ({
      day: r.day,
      total: parseFloat(r.total) || 0,
      count: parseInt(r.count) || 0
    }));
    res.json({ success: true, data });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

/** GET /analytics/peak-hours — Busiest hours ranking (last 30 days) */
app.get('/analytics/peak-hours', async (req, res) => {
  try {
    const rows = await query(`
      SELECT HOUR(created_at) as hour, COUNT(*) as bookings
      FROM console_booking
      WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
      GROUP BY HOUR(created_at)
      ORDER BY bookings DESC
    `);
    const data = rows.map(r => ({
      hour: parseInt(r.hour),
      hour_label: `${String(r.hour).padStart(2, '0')}:00`,
      bookings: parseInt(r.bookings)
    }));
    res.json({ success: true, data });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

/** GET /analytics/popular-games — Top games by play count */
app.get('/analytics/popular-games', async (req, res) => {
  try {
    const rows = await query(`
      SELECT g.game_title, COUNT(*) as times_played
      FROM console_games g
      GROUP BY g.game_title
      ORDER BY times_played DESC
      LIMIT 10
    `);
    const data = rows.map(r => ({
      game_title: r.game_title,
      times_played: parseInt(r.times_played)
    }));
    res.json({ success: true, data });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

/** GET /analytics/member-growth — New members per day (last 30 days) */
app.get('/analytics/member-growth', async (req, res) => {
  try {
    const rows = await query(`
      SELECT DATE(created_at) as day, COUNT(*) as new_members
      FROM members
      WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
      GROUP BY DATE(created_at)
      ORDER BY day ASC
    `);
    const data = rows.map(r => ({
      day: r.day,
      new_members: parseInt(r.new_members)
    }));
    // Also include total members
    const totalRow = await query(`SELECT COUNT(*) as total FROM members`);
    const total = totalRow[0] ? parseInt(totalRow[0].total) : 0;
    res.json({ success: true, data, total_members: total });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

/** GET /analytics/forecast — 7-day moving average revenue forecast */
app.get('/analytics/forecast', async (req, res) => {
  try {
    // Get daily totals for last 14 days to compute 7-day MA
    const rows = await query(`
      SELECT DATE(sale_date) as day, COALESCE(SUM(amount), 0) as daily_total
      FROM sales_daily
      WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
      GROUP BY DATE(sale_date)
      ORDER BY day ASC
    `);

    const dailyTotals = rows.map(r => ({
      day: r.day,
      daily_total: parseFloat(r.daily_total) || 0
    }));

    // Compute 7-day moving average
    let forecast = 0;
    if (dailyTotals.length >= 7) {
      const last7 = dailyTotals.slice(-7);
      forecast = last7.reduce((sum, d) => sum + d.daily_total, 0) / 7;
    } else if (dailyTotals.length > 0) {
      forecast = dailyTotals.reduce((sum, d) => sum + d.daily_total, 0) / dailyTotals.length;
    }

    // Get current month and last month totals for trend direction
    const currentMonth = await query(`
      SELECT COALESCE(SUM(amount), 0) as total
      FROM sales_daily
      WHERE MONTH(sale_date) = MONTH(CURDATE()) AND YEAR(sale_date) = YEAR(CURDATE())
    `);
    const lastMonth = await query(`
      SELECT COALESCE(SUM(amount), 0) as total
      FROM sales_daily
      WHERE MONTH(sale_date) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        AND YEAR(sale_date) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
    `);

    const currentMonthTotal = parseFloat(currentMonth[0]?.total) || 0;
    const lastMonthTotal = parseFloat(lastMonth[0]?.total) || 0;
    const trend = lastMonthTotal > 0
      ? ((currentMonthTotal - lastMonthTotal) / lastMonthTotal * 100).toFixed(1)
      : 0;

    res.json({
      success: true,
      data: {
        forecast: Math.round(forecast * 100) / 100,
        projected_7day: Math.round(forecast * 7 * 100) / 100,
        trend_pct: parseFloat(trend),
        current_month_total: currentMonthTotal,
        last_month_total: lastMonthTotal
      }
    });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

/** GET /analytics/summary — All analytics in one call */
app.get('/analytics/summary', async (req, res) => {
  try {
    // Run all queries in parallel
    const [salesTrend, peakHours, popularGames, memberGrowth, forecast] = await Promise.all([
      query(`SELECT DATE(sale_date) as day, COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM sales_daily WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) GROUP BY DATE(sale_date) ORDER BY day ASC`),
      query(`SELECT HOUR(created_at) as hour, COUNT(*) as bookings FROM console_booking WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY HOUR(created_at) ORDER BY bookings DESC`),
      query(`SELECT g.game_title, COUNT(*) as times_played FROM console_games g GROUP BY g.game_title ORDER BY times_played DESC LIMIT 10`),
      query(`SELECT DATE(created_at) as day, COUNT(*) as new_members FROM members WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY DATE(created_at) ORDER BY day ASC`),
      query(`SELECT DATE(sale_date) as day, COALESCE(SUM(amount), 0) as daily_total FROM sales_daily WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY) GROUP BY DATE(sale_date) ORDER BY day ASC`)
    ]);

    // Format sales trend
    const salesTrendData = salesTrend.map(r => ({
      day: r.day, total: parseFloat(r.total) || 0, count: parseInt(r.count) || 0
    }));

    // Format peak hours
    const peakHoursData = peakHours.map(r => ({
      hour: parseInt(r.hour), hour_label: `${String(r.hour).padStart(2, '0')}:00`, bookings: parseInt(r.bookings)
    }));

    // Format popular games
    const popularGamesData = popularGames.map(r => ({
      game_title: r.game_title, times_played: parseInt(r.times_played)
    }));

    // Format member growth
    const memberGrowthData = memberGrowth.map(r => ({
      day: r.day, new_members: parseInt(r.new_members)
    }));

    // Compute forecast (7-day moving average)
    const dailyTotals = forecast.map(r => ({ day: r.day, daily_total: parseFloat(r.daily_total) || 0 }));
    let forecastVal = 0;
    if (dailyTotals.length >= 7) {
      const last7 = dailyTotals.slice(-7);
      forecastVal = last7.reduce((sum, d) => sum + d.daily_total, 0) / 7;
    } else if (dailyTotals.length > 0) {
      forecastVal = dailyTotals.reduce((sum, d) => sum + d.daily_total, 0) / dailyTotals.length;
    }

    // Get total members count and month-over-month comparison
    const [totalMembersRow, currentMonth, lastMonth] = await Promise.all([
      query('SELECT COUNT(*) as total FROM members'),
      query('SELECT COALESCE(SUM(amount), 0) as total FROM sales_daily WHERE MONTH(sale_date) = MONTH(CURDATE()) AND YEAR(sale_date) = YEAR(CURDATE())'),
      query('SELECT COALESCE(SUM(amount), 0) as total FROM sales_daily WHERE MONTH(sale_date) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) AND YEAR(sale_date) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))')
    ]);
    const totalMembers = parseInt(totalMembersRow[0]?.total) || 0;
    const currentMonthTotal = parseFloat(currentMonth[0]?.total) || 0;
    const lastMonthTotal = parseFloat(lastMonth[0]?.total) || 0;
    const trendPct = lastMonthTotal > 0 ? ((currentMonthTotal - lastMonthTotal) / lastMonthTotal * 100) : 0;

    res.json({
      success: true,
      data: {
        sales_trend: salesTrendData,
        peak_hours: peakHoursData,
        popular_games: popularGamesData,
        member_growth: memberGrowthData,
        total_members: totalMembers,
        forecast: {
          daily_forecast: Math.round(forecastVal * 100) / 100,
          projected_7day: Math.round(forecastVal * 7 * 100) / 100,
          trend_pct: Math.round(trendPct * 10) / 10,
          current_month_total: currentMonthTotal,
          last_month_total: lastMonthTotal
        }
      }
    });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── Start Server ───
const PORT = process.env.PORT || 3120;
app.listen(PORT, '127.0.0.1', () => {
  console.log(`[predictive-analytics] Server running on port ${PORT}`);
});
