#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read the index.html file
const indexPath = path.join(__dirname, '../dist/index.html');
let htmlContent = fs.readFileSync(indexPath, 'utf8');

// Environment variables for Ackee
const ackeeServerUrl = process.env.ACKEE_SERVER_URL || '';
const ackeeDomainId = process.env.ACKEE_DOMAIN_ID || '';

// Inject Ackee script if both variables are provided
if (ackeeServerUrl && ackeeDomainId) {
  // Check if Ackee script is already injected
  if (htmlContent.includes('data-ackee-server')) {
    console.log('Ackee tracking script already present - skipping injection');
  } else {
    const ackeeScript = `
    <script async src="${ackeeServerUrl}/tracker.js" data-ackee-server="${ackeeServerUrl}" data-ackee-domain-id="${ackeeDomainId}"></script>`;
    
    // Insert before closing head tag
    htmlContent = htmlContent.replace('</head>', `${ackeeScript}\n  </head>`);
    
    console.log('Ackee tracking script injected');
  }
} else {
  console.log('Ackee tracking not configured - skipping injection');
}

// Write the modified content back
fs.writeFileSync(indexPath, htmlContent, 'utf8');

console.log('Environment injection completed');