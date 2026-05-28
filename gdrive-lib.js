const crypto = require('crypto');
const https = require('https');
const fs = require('fs');

function signJwt(key, email, scope) {
  const header = { alg: 'RS256', typ: 'JWT' };
  const iat = Math.floor(Date.now() / 1000);
  const exp = iat + 3600;
  const claimSet = {
    iss: email,
    scope: scope,
    aud: 'https://oauth2.googleapis.com/token',
    exp: exp,
    iat: iat
  };
  const base64Header = Buffer.from(JSON.stringify(header)).toString('base64url');
  const base64ClaimSet = Buffer.from(JSON.stringify(claimSet)).toString('base64url');
  const sign = crypto.createSign('RSA-SHA256');
  sign.update(base64Header + '.' + base64ClaimSet);
  const signature = sign.sign(key, 'base64url');
  return base64Header + '.' + base64ClaimSet + '.' + signature;
}

function requestAccessToken(jwt) {
  return new Promise((resolve, reject) => {
    const postData = new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt
    }).toString();
    const req = https.request('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(body);
          if (parsed.access_token) resolve(parsed.access_token);
          else reject(new Error("No access token: " + body));
        } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function getAccessToken() {
  const saPath = '/home/node/.openclaw/workspace/service-account.json';
  if (!fs.existsSync(saPath)) {
    throw new Error("service-account.json not found in workspace.");
  }
  const sa = JSON.parse(fs.readFileSync(saPath, 'utf8'));
  const jwt = signJwt(sa.private_key, sa.client_email, 'https://www.googleapis.com/auth/drive.readonly');
  return await requestAccessToken(jwt);
}

function apiRequest(token, url, options = {}) {
  return new Promise((resolve, reject) => {
    const mergedOptions = {
      headers: { 
        'Authorization': `Bearer ${token}`,
        ...options.headers
      },
      ...options
    };
    https.get(url, mergedOptions, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); }
        catch (e) { reject(new Error(`Failed to parse response: ${body}`)); }
      });
    }).on('error', reject);
  });
}

async function listFilesInFolder(folderId) {
  const token = await getAccessToken();
  const q = encodeURIComponent(`'${folderId}' in parents and trashed = false`);
  const url = `https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id,name,mimeType,size,modifiedTime)`;
  return await apiRequest(token, url);
}

async function searchFiles(queryStr) {
  const token = await getAccessToken();
  const q = encodeURIComponent(queryStr);
  const url = `https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id,name,mimeType,parents,size,modifiedTime)`;
  return await apiRequest(token, url);
}

module.exports = {
  getAccessToken,
  listFilesInFolder,
  searchFiles,
  apiRequest
};
