#!/usr/bin/env node
/**
 * Generates full Postman collection for Universal Data Format Converter API.
 * Run: node scripts/generate-postman-collection.js
 */

const fs = require('fs');
const path = require('path');

const INPUTS = ['json','xml','csv','tsv','excel','yaml','ndjson','sql-insert','html-table','env','query-string','base64'];
const OUTPUTS = [...INPUTS, 'pdf'];

const SAMPLES = {
  json: { name: 'John', age: 30 },
  xml: '<root><name>John</name><age>30</age></root>',
  csv: 'name,age\nJohn,30\nJane,25',
  tsv: 'name\tage\nJohn\t30\nJane\t25',
  excel: '',  // base64 - placeholder
  yaml: 'name: John\nage: 30',
  ndjson: '{"name":"John","age":30}\n{"name":"Jane","age":25}',
  'sql-insert': "INSERT INTO users (name, age) VALUES ('John', 30), ('Jane', 25);",
  'html-table': '<table><tr><th>name</th><th>age</th></tr><tr><td>John</td><td>30</td></tr></table>',
  env: 'FOO=bar\nBAZ=qux',
  'query-string': 'name=John&age=30',
  base64: 'eyJuYW1lIjoiSm9obiIsImFnZSI6MzB9'
};

const ACCEPT_BY_TO = {
  json: 'application/json',
  xml: 'application/xml',
  csv: 'text/csv',
  tsv: 'text/tab-separated-values',
  excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  yaml: 'text/yaml',
  ndjson: 'application/x-ndjson',
  'sql-insert': 'text/plain',
  'html-table': 'text/html',
  env: 'text/plain',
  'query-string': 'text/plain',
  base64: 'text/plain',
  pdf: 'application/pdf'
};

function createRequest(from, to) {
  let data = SAMPLES[from];
  if (from === 'json') data = [SAMPLES.json, { name: 'Jane', age: 25 }];
  else if (from === 'excel') data = SAMPLES.base64;  // placeholder - user replaces with real base64 xlsx
  const body = { from, to, data };
  if (to === 'sql-insert') body.options = { output: { sqlInsert: { tableName: 'users' } } };
  return {
    name: `${from} → ${to}`,
    request: {
      method: 'POST',
      header: [
        { key: 'Content-Type', value: 'application/json' },
        { key: 'Accept', value: ACCEPT_BY_TO[to] || 'text/plain' },
        { key: 'x-rapidapi-key', value: '{{rapidapi_key}}', type: 'text' },
        { key: 'x-rapidapi-host', value: 'universal-data-format-converter.p.rapidapi.com', type: 'text' }
      ],
      body: {
        mode: 'raw',
        raw: JSON.stringify(body, null, 2)
      },
      url: {
        raw: 'https://universal-data-format-converter.p.rapidapi.com/convert',
        protocol: 'https',
        host: ['universal-data-format-converter', 'p', 'rapidapi', 'com'],
        path: ['convert']
      }
    }
  };
}

const folders = INPUTS.map(from => ({
  name: `From ${from}`,
  item: OUTPUTS.map(to => createRequest(from, to))
}));

const collection = {
  info: {
    name: 'Universal Data Format Converter API',
    description: 'Full collection for all format conversions. Set rapidapi_key in collection variables.',
    schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
  },
  variable: [
    { key: 'rapidapi_key', value: 'YOUR_RAPIDAPI_KEY', type: 'string' }
  ],
  item: folders
};

const outPath = path.join(__dirname, '../apis/universal-data-format-converter-postman.json');
fs.writeFileSync(outPath, JSON.stringify(collection, null, 2));
console.log('Generated', outPath);
