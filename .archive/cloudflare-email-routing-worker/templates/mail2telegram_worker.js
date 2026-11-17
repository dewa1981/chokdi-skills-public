// mail2telegram v4 — Cloudflare Email Worker: MIME parse → clean text → Telegram,
// plus auto-reply hook for Addy.io verification emails (unfamiliar-domain flow).
// Env vars required: TELEGRAM_TOKEN (Secret), TELEGRAM_ID (plain Text).
import { EmailMessage } from "cloudflare:email";

export default {
  async email(message, env, ctx) {
    try {
      const from = message.from || '';
      const subject = message.headers.get('subject') || '';
      const to = message.to || '';

      // ===== AUTO-REPLY for Addy.io verification emails =====
      // Addy requires a reply from the SAME address for unfamiliar domains.
      if (from.includes('verify.addy.io') && /verify your email/i.test(subject)) {
        try {
          const messageId = message.headers.get('message-id') || '';
          const domain = to.split('@')[1] || 'banknotif.com';
          const raw = [
            'From: ' + to,
            'To: ' + from,
            'Subject: Re: ' + subject,
            messageId ? 'In-Reply-To: ' + messageId : '',
            messageId ? 'References: ' + messageId : '',
            'Message-ID: <reply-' + Date.now() + '@' + domain + '>',
            'Date: ' + new Date().toUTCString(),
            'MIME-Version: 1.0',
            'Content-Type: text/plain; charset=utf-8',
            'Content-Transfer-Encoding: 7bit',
            '',
            'ok',
            ''
          ].join('\r\n');
          await message.reply(new EmailMessage(to, from, raw));
          console.log('AUTO-REPLY verifikasi Addy berhasil');
          await tgSend(env, '✅ AUTO-REPLY ke Addy berhasil! Link verifikasi menyusul...');
        } catch (e) {
          console.log('Auto-reply gagal:', e.message || String(e));
          await tgSend(env, '⚠️ Auto-reply gagal: ' + (e.message || String(e)).slice(0, 200));
        }
      }

      // ===== Parse email body (headers/body split + multipart + decode) =====
      const rawEmail = await streamToText(message.raw);
      const sep = rawEmail.indexOf('\r\n\r\n');
      const headerBlock = sep >= 0 ? rawEmail.slice(0, sep) : rawEmail;
      let bodyPart = sep >= 0 ? rawEmail.slice(sep + 4) : '';
      const ctMatch = headerBlock.match(/content-type:\s*([^\r\n]+)/i);
      const contentType = ctMatch ? ctMatch[1] : 'text/plain';
      const boundaryMatch = contentType.match(/boundary="?([^";]+)"?/i);
      const boundary = boundaryMatch ? boundaryMatch[1] : null;
      let text = '';
      if (boundary) {
        const parts = bodyPart.split('--' + boundary);
        let htmlPart = '';
        for (const part of parts) {
          const pSep = part.indexOf('\r\n\r\n');
          if (pSep < 0) continue;
          const pHeader = part.slice(0, pSep);
          const pBody = part.slice(pSep + 4);
          if (/content-type:\s*text\/plain/i.test(pHeader)) {
            text = decodePart(pBody, pHeader);
            break;
          }
          if (!htmlPart && /content-type:\s*text\/html/i.test(pHeader)) {
            htmlPart = decodePart(pBody, pHeader);
          }
        }
        if (!text) text = htmlPart;
      } else {
        text = decodePart(bodyPart, headerBlock);
      }
      let clean = htmlToText(text);
      if (clean.length > 2500) clean = clean.slice(0, 2500) + '…';

      const msg = '📧 EMAIL MASUK\n' +
        '👤 Dari: ' + from.slice(0, 100) + '\n' +
        '📌 Subjek: ' + subject.slice(0, 150) + '\n' +
        '━━━━━━━━━━━\n' + clean;
      await tgSend(env, msg);
    } catch (e) {
      console.log('Worker error:', e.message || String(e));
    }
  }
};

async function tgSend(env, text) {
  try {
    const resp = await fetch('https://api.telegram.org/bot' + env.TELEGRAM_TOKEN + '/sendMessage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: env.TELEGRAM_ID, text: text, disable_web_page_preview: true })
    });
    const out = await resp.text();
    if (!out.includes('"ok":true')) {
      console.log('TG send gagal:', out.slice(0, 300));
    }
  } catch (e) {
    console.log('TG error:', e.message || String(e));
  }
}

async function streamToText(stream) {
  const reader = stream.getReader();
  const chunks = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  const buf = new Uint8Array(chunks.reduce((a, c) => a + c.length, 0));
  let off = 0;
  for (const c of chunks) { buf.set(c, off); off += c.length; }
  return new TextDecoder().decode(buf);
}

function decodePart(body, partHeaders) {
  let out = body;
  const encMatch = partHeaders.match(/content-transfer-encoding:\s*([^\r\n]+)/i);
  const enc = encMatch ? encMatch[1].trim().toLowerCase() : '';
  if (enc === 'base64') {
    try {
      const b64 = out.replace(/\s+/g, '');
      const bin = atob(b64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      out = new TextDecoder().decode(bytes);
    } catch (e) {}
  } else if (enc === 'quoted-printable') {
    out = out.replace(/=\r?\n/g, '').replace(/=([0-9A-Fa-f]{2})/g, (m, h) => String.fromCharCode(parseInt(h, 16)));
  }
  return out;
}

function htmlToText(html) {
  if (!/<[a-z][\s\S]*>/i.test(html)) {
    return html.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  }
  return html
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<head[\s\S]*?<\/head>/gi, ' ')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>|<\/div>|<\/tr>|<\/h[1-6]>|<\/li>/gi, '\n')
    .replace(/<a[^>]*href="([^"]*)"[^>]*>/gi, ' [$1] ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&mdash;/g, '—').replace(/&ndash;/g, '–').replace(/&hellip;/g, '…')
    .replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}
