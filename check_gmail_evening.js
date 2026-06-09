#!/usr/bin/env node
/**
 * Evening Gmail Check - Cron Job (Node.js)
 * Checks for unread/recent emails, especially from Nova about Personal-Wallet-Tele-Bot-2 handover.
 */
const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');
const readline = require('readline');

const TOKEN_PATH = path.join(__dirname, 'token.json');
const SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'];
const NOVA_EMAIL = 'yeyintoo12345678@gmail.com';

function loadCredentials() {
  if (!fs.existsSync(TOKEN_PATH)) {
    throw new Error(`Token not found at ${TOKEN_PATH}`);
  }
  const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
  const { client_id, client_secret, refresh_token } = token;
  
  const oauth2Client = new google.auth.OAuth2(client_id, client_secret);
  oauth2Client.setCredentials({ refresh_token });
  return oauth2Client;
}

function decodeBase64(data) {
  return Buffer.from(data.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf-8');
}

function getBodyFromPayload(payload) {
  // Direct body
  if (payload.body && payload.body.data) {
    return decodeBase64(payload.body.data);
  }
  
  // Walk through parts
  if (payload.parts) {
    for (const part of payload.parts) {
      if (part.mimeType === 'text/plain' && part.body && part.body.data) {
        return decodeBase64(part.body.data);
      }
      if (part.parts) {
        for (const subpart of part.parts) {
          if (subpart.mimeType === 'text/plain' && subpart.body && subpart.body.data) {
            return decodeBase64(subpart.body.data);
          }
        }
      }
    }
  }
  
  return '[Body could not be decoded]';
}

async function getEmailBody(gmail, msgId) {
  const res = await gmail.users.messages.get({
    userId: 'me',
    id: msgId,
    format: 'full',
  });
  const payload = res.data.payload || {};
  return getBodyFromPayload(payload);
}

async function listRecentEmails(gmail, maxResults = 20) {
  const res = await gmail.users.messages.list({
    userId: 'me',
    q: 'newer_than:1d',
    maxResults,
  });
  
  const messages = res.data.messages || [];
  if (!messages.length) return [];
  
  const emailList = [];
  for (const msg of messages) {
    const meta = await gmail.users.messages.get({
      userId: 'me',
      id: msg.id,
      format: 'metadata',
      metadataHeaders: ['From', 'To', 'Subject', 'Date'],
    });
    
    const headers = {};
    (meta.data.payload.headers || []).forEach(h => {
      headers[h.name] = h.value;
    });
    
    const isUnread = (meta.data.labelIds || []).includes('UNREAD');
    
    emailList.push({
      id: msg.id,
      from: headers['From'] || 'Unknown',
      to: headers['To'] || 'Unknown',
      subject: headers['Subject'] || '(No Subject)',
      date: headers['Date'] || 'Unknown',
      unread: isUnread,
      labels: meta.data.labelIds || [],
    });
  }
  
  return emailList;
}

async function main() {
  const now = new Date().toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
  const output = [];
  const sep = '='.repeat(60);
  
  output.push(sep);
  output.push('📧 Evening Gmail Inbox Check');
  output.push(`🕐 Time: ${now}`);
  output.push(sep);
  
  try {
    const auth = loadCredentials();
    const gmail = google.gmail({ version: 'v1', auth });
    
    // Profile
    const profile = await gmail.users.getProfile({ userId: 'me' });
    output.push(`📫 Account: ${profile.data.emailAddress}`);
    output.push('');
    
    // List emails
    const emails = await listRecentEmails(gmail);
    
    if (!emails.length) {
      output.push('📭 No emails found in the last 24 hours.');
      output.push('');
      output.push(sep);
      output.push('CONCLUSION: NO_REPLY — No recent emails found.');
      console.log(output.join('\n'));
      return { status: 'NO_REPLY' };
    }
    
    const fromNova = [];
    const important = [];
    const promotional = [];
    const other = [];
    
    for (const e of emails) {
      const subject = e.subject.toLowerCase();
      const fromAddr = e.from.toLowerCase();
      
      // Nova check
      if (fromAddr.includes(NOVA_EMAIL)) {
        fromNova.push(e);
        important.push(e);
        continue;
      }
      
      // Promo check
      const promoKeywords = ['unsubscribe', 'marketing', 'promotions', 'newsletter', 'sale', 'discount',
        'promo', 'spam', 'advertisement', 'you won', 'lottery', 'prize'];
      const promoDomains = ['marketing', 'newsletter', 'mailchimp', 'sendgrid', 'hubspot',
        'constantcontact', 'campaign', 'bulk', 'info@', 'noreply@', 'no-reply@'];
      
      let isPromo = false;
      for (const kw of promoKeywords) {
        if (subject.includes(kw) || fromAddr.includes(kw)) { isPromo = true; break; }
      }
      if (!isPromo) {
        for (const d of promoDomains) {
          if (fromAddr.includes(d)) { isPromo = true; break; }
        }
      }
      
      if (isPromo) {
        promotional.push(e);
        continue;
      }
      
      // Important check
      const importantKeywords = ['handover', 'wallet', 'personal-wallet-tele-bot', 'nova',
        'reply', 'urgent', 'important', 'payment', 'transfer',
        'bot-2', 'bot 2', 'password', 'token', 'security'];
      let isImportant = false;
      for (const kw of importantKeywords) {
        if (subject.includes(kw)) { isImportant = true; break; }
      }
      
      if (isImportant) {
        important.push(e);
      } else {
        other.push(e);
      }
    }
    
    // Print Nova emails
    const novaBodies = {};
    if (fromNova.length) {
      output.push('📩 ** EMAILS FROM NOVA (yeyintoo12345678@gmail.com) **');
      output.push('-'.repeat(60));
      for (const e of fromNova) {
        const status = e.unread ? '🔴 UNREAD' : '✅ Read';
        output.push(`  From: ${e.from}`);
        output.push(`  Subject: ${e.subject}`);
        output.push(`  Date: ${e.date}`);
        output.push(`  Status: ${status}`);
        const body = await getEmailBody(gmail, e.id);
        novaBodies[e.id] = body;
        output.push(`  Body preview: ${body.slice(0, 400)}`);
        output.push('');
      }
    }
    
    // Other important
    const nonNovaImportant = important.filter(e => !fromNova.includes(e));
    if (nonNovaImportant.length) {
      output.push('📌 ** OTHER IMPORTANT EMAILS **');
      output.push('-'.repeat(60));
      for (const e of nonNovaImportant) {
        const status = e.unread ? '🔴 UNREAD' : '✅ Read';
        output.push(`  From: ${e.from}`);
        output.push(`  Subject: ${e.subject}`);
        output.push(`  Status: ${status}`);
        output.push('');
      }
    }
    
    // Regular
    if (other.length) {
      output.push(`📋 Regular emails (${other.length}):`);
      for (const e of other) {
        const status = e.unread ? '🆕' : '📖';
        output.push(`  ${status} ${e.from.slice(0, 40)} — ${e.subject.slice(0, 60)}`);
      }
      output.push('');
    }
    
    // Promo skipped
    if (promotional.length) {
      output.push(`📪 Skipped promotional/newsletter emails: ${promotional.length}`);
      for (const e of promotional.slice(0, 3)) {
        output.push(`   • ${e.from.slice(0, 40)} — ${e.subject.slice(0, 50)}`);
      }
      if (promotional.length > 3) {
        output.push(`   ... and ${promotional.length - 3} more`);
      }
      output.push('');
    }
    
    // Conclusion
    output.push(sep);
    output.push('📊 CONCLUSION:');
    output.push(`   Total recent emails: ${emails.length}`);
    output.push(`   From Nova: ${fromNova.length}`);
    output.push(`   Important (other): ${nonNovaImportant.length}`);
    output.push(`   Regular: ${other.length}`);
    output.push(`   Promotional (skipped): ${promotional.length}`);
    
    let result = { status: 'NOTHING' };
    
    if (fromNova.length) {
      output.push('\n⚠️  NOVA REPLIED! ⚠️');
      const novaDetails = [];
      for (const e of fromNova) {
        const body = novaBodies[e.id] || await getEmailBody(gmail, e.id);
        output.push(`\n📝 Full body from Nova (${e.subject}):`);
        output.push(body.slice(0, 800));
        if (body.length > 800) output.push('...');
        novaDetails.push({ subject: e.subject, from: e.from, body: body.slice(0, 500) });
      }
      result = { status: 'NOVA_REPLY', novaEmails: novaDetails };
    } else if (nonNovaImportant.length) {
      output.push('\n📌 Important emails found (non-Nova).');
      result = { status: 'IMPORTANT', count: nonNovaImportant.length, emails: nonNovaImportant.map(e => ({ from: e.from, subject: e.subject })) };
    } else {
      output.push('\n✅ Nothing significant — no important or Nova emails found.');
    }
    
    console.log(output.join('\n'));
    return result;
    
  } catch (err) {
    output.push(`\n❌ ERROR: ${err.message}`);
    output.push(err.stack);
    console.log(output.join('\n'));
    return { status: 'ERROR', message: err.message };
  }
}

main()
  .then(result => {
    // Output structured result for parsing
    console.log(`\n---RESULT:${JSON.stringify(result)}---`);
  })
  .catch(err => {
    console.error('Fatal error:', err);
    console.log(`\n---RESULT:${JSON.stringify({ status: 'FATAL_ERROR', message: err.message })}---`);
  });
