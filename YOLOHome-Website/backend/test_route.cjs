const http = require('http');
const req = http.request({
  hostname: 'localhost',
  port: 5000,
  path: '/api/voice/command',
  method: 'POST',
  headers: {
    'Content-Type': 'multipart/form-data; boundary=--------------------------1234567890'
  }
}, (res) => {
  console.log('STATUS:', res.statusCode);
  res.setEncoding('utf8');
  res.on('data', (chunk) => console.log('BODY:', chunk));
});
req.on('error', (e) => console.error('problem with request:', e.message));
req.write('----------------------------1234567890\r\nContent-Disposition: form-data; name="audio"; filename="test.wav"\r\nContent-Type: audio/wav\r\n\r\nfakeaudio\r\n----------------------------1234567890--\r\n');
req.end();
