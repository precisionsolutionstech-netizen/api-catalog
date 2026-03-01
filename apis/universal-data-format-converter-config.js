/**
 * Options schema and sample data for Universal Data Format Converter API.
 * Used by universal-data-format-converter.html
 */
(function(global){
    var FORMAT_TO_OPTION_KEY = {
        'json':'json','xml':'xml','csv':'csv','tsv':'tsv','excel':'excel','yaml':'yaml',
        'ndjson':'ndjson','sql-insert':'sqlInsert','html-table':'htmlTable','env':'env',
        'query-string':'queryString','base64':'base64','pdf':'pdf'
    };

    var OPTIONS_SCHEMA = {
        input: {
            'json': [
                { key: 'parseDates', type: 'boolean', default: true, desc: 'Convert ISO strings to Date' },
                { key: 'maxDepth', type: 'number', default: 200, desc: 'Maximum nesting depth' },
                { key: 'allowComments', type: 'boolean', default: false, desc: 'JSON5-like comments' }
            ],
            'xml': [
                { key: 'preserveAttributes', type: 'boolean', default: true },
                { key: 'attributeMode', enum: ['_attributes','prefix'], default: '_attributes' },
                { key: 'stripNamespaces', type: 'boolean', default: true },
                { key: 'parseNumbers', type: 'boolean', default: true },
                { key: 'parseBooleans', type: 'boolean', default: true },
                { key: 'allowMixedContent', type: 'boolean', default: false },
                { key: 'maxDepth', type: 'number', default: 200 }
            ],
            'csv': [
                { key: 'delimiter', type: 'string', default: ',', desc: 'Field delimiter' },
                { key: 'quoteChar', type: 'string', default: '"' },
                { key: 'escapeChar', type: 'string', default: '"' },
                { key: 'hasHeader', type: 'boolean', default: true },
                { key: 'trim', type: 'boolean', default: true },
                { key: 'strictColumns', type: 'boolean', default: false },
                { key: 'detectTypes', type: 'boolean', default: true }
            ],
            'tsv': [
                { key: 'delimiter', type: 'string', default: '\\t', desc: 'Defaults to tab' },
                { key: 'quoteChar', type: 'string', default: '"' },
                { key: 'hasHeader', type: 'boolean', default: true },
                { key: 'trim', type: 'boolean', default: true },
                { key: 'strictColumns', type: 'boolean', default: false },
                { key: 'detectTypes', type: 'boolean', default: true }
            ],
            'excel': [
                { key: 'sheets', type: 'string', default: 'all', desc: 'Sheet names or "all"' },
                { key: 'headerRow', type: 'number', default: 1 },
                { key: 'range', type: 'string', default: '', desc: 'Cell range (optional)' },
                { key: 'detectTypes', type: 'boolean', default: true },
                { key: 'trim', type: 'boolean', default: true },
                { key: 'emptyAsNull', type: 'boolean', default: true }
            ],
            'yaml': [
                { key: 'schema', enum: ['core','json'], default: 'core' },
                { key: 'allowAnchors', type: 'boolean', default: true },
                { key: 'parseDates', type: 'boolean', default: true },
                { key: 'parseBooleans', type: 'boolean', default: true },
                { key: 'maxDepth', type: 'number', default: 200 }
            ],
            'ndjson': [
                { key: 'strict', type: 'boolean', default: true },
                { key: 'skipInvalidLines', type: 'boolean', default: false }
            ],
            'sql-insert': [
                { key: 'dialect', enum: ['postgres','mysql','sqlite'], default: 'postgres' },
                { key: 'strict', type: 'boolean', default: true }
            ],
            'html-table': [
                { key: 'tableIndex', type: 'number', default: 0 },
                { key: 'trim', type: 'boolean', default: true },
                { key: 'detectTypes', type: 'boolean', default: true }
            ],
            'env': [
                { key: 'allowComments', type: 'boolean', default: true },
                { key: 'trim', type: 'boolean', default: true }
            ],
            'query-string': [
                { key: 'parseArrays', type: 'boolean', default: true },
                { key: 'parseBooleans', type: 'boolean', default: true },
                { key: 'parseNumbers', type: 'boolean', default: true }
            ],
            'base64': [
                { key: 'decode', type: 'boolean', default: true }
            ]
        },
        output: {
            'json': [
                { key: 'pretty', type: 'boolean', default: true },
                { key: 'indent', type: 'number', default: 2 },
                { key: 'sortKeys', type: 'boolean', default: false }
            ],
            'xml': [
                { key: 'rootName', type: 'string', default: 'root' },
                { key: 'pretty', type: 'boolean', default: true },
                { key: 'includeXmlDeclaration', type: 'boolean', default: true },
                { key: 'nullHandling', enum: ['emptyTag','omit'], default: 'emptyTag' },
                { key: 'attributeMode', enum: ['_attributes','prefix'], default: '_attributes' },
                { key: 'encoding', type: 'string', default: 'UTF-8' }
            ],
            'csv': [
                { key: 'delimiter', type: 'string', default: ',' },
                { key: 'includeHeader', type: 'boolean', default: true },
                { key: 'flatten', type: 'boolean', default: true },
                { key: 'flattenSeparator', type: 'string', default: '.' },
                { key: 'nullValue', type: 'string', default: '' },
                { key: 'encoding', type: 'string', default: 'UTF-8' }
            ],
            'tsv': [
                { key: 'delimiter', type: 'string', default: '\\t' },
                { key: 'includeHeader', type: 'boolean', default: true },
                { key: 'flatten', type: 'boolean', default: true },
                { key: 'flattenSeparator', type: 'string', default: '.' },
                { key: 'nullValue', type: 'string', default: '' }
            ],
            'excel': [
                { key: 'sheetName', type: 'string', default: 'Sheet1' },
                { key: 'multiSheetMode', enum: ['single','multi'], default: 'multi' },
                { key: 'autoWidth', type: 'boolean', default: true },
                { key: 'nullAsEmpty', type: 'boolean', default: true }
            ],
            'yaml': [
                { key: 'indent', type: 'number', default: 2 },
                { key: 'lineWidth', type: 'number', default: 80 },
                { key: 'sortKeys', type: 'boolean', default: false }
            ],
            'ndjson': [
                { key: 'newlineDelimited', type: 'boolean', default: true }
            ],
            'sql-insert': [
                { key: 'tableName', type: 'string', default: 'users', required: true },
                { key: 'dialect', enum: ['postgres','mysql','sqlite'], default: 'postgres' },
                { key: 'batchSize', type: 'number', default: 1000 },
                { key: 'quoteIdentifiers', type: 'boolean', default: true }
            ],
            'html-table': [
                { key: 'includeThead', type: 'boolean', default: true },
                { key: 'tableClass', type: 'string', default: '', desc: 'CSS class for table' },
                { key: 'pretty', type: 'boolean', default: true },
                { key: 'escapeHtml', type: 'boolean', default: true }
            ],
            'env': [
                { key: 'uppercaseKeys', type: 'boolean', default: false },
                { key: 'sortKeys', type: 'boolean', default: false }
            ],
            'query-string': [
                { key: 'arrayFormat', enum: ['repeat','brackets'], default: 'repeat' },
                { key: 'encode', type: 'boolean', default: true }
            ],
            'pdf': [
                { key: 'pageSize', enum: ['A4','Letter'], default: 'A4' },
                { key: 'orientation', enum: ['portrait','landscape'], default: 'portrait' },
                { key: 'repeatHeader', type: 'boolean', default: true },
                { key: 'fontFamily', type: 'string', default: 'Helvetica' },
                { key: 'fontSize', type: 'number', default: 10 },
                { key: 'wrapText', type: 'boolean', default: true },
                { key: 'title', type: 'string', default: '' },
                { key: 'includeGeneratedAt', type: 'boolean', default: false }
            ]
        }
    };

    var SAMPLES = {
        json: { name: 'John', age: 30 },
        xml: '<root><name>John</name><age>30</age></root>',
        csv: 'name,age\nJohn,30\nJane,25',
        tsv: 'name\tage\nJohn\t30\nJane\t25',
        excel: '', // base64 - user must provide
        yaml: 'name: John\nage: 30',
        ndjson: '{"name":"John","age":30}\n{"name":"Jane","age":25}',
        'sql-insert': "INSERT INTO users (name, age) VALUES ('John', 30), ('Jane', 25);",
        'html-table': '<table><tr><th>name</th><th>age</th></tr><tr><td>John</td><td>30</td></tr></table>',
        env: 'FOO=bar\nBAZ=qux',
        'query-string': 'name=John&age=30',
        base64: (function(){ try { return btoa(unescape(encodeURIComponent(JSON.stringify({ name: 'John', age: 30 })))); } catch(e){ return 'eyJuYW1lIjoiSm9obiIsImFnZSI6MzB9'; } })()
    };

    // Map format id (kebab) to option key (camel) for API
    var formatToOptionKey = function(f) {
        return { 'json':'json','xml':'xml','csv':'csv','tsv':'tsv','excel':'excel','yaml':'yaml',
            'ndjson':'ndjson','sql-insert':'sqlInsert','html-table':'htmlTable','env':'env',
            'query-string':'queryString','base64':'base64','pdf':'pdf' }[f] || f;
    };

    global.UDCF_OPTIONS_SCHEMA = OPTIONS_SCHEMA;
    global.UDCF_SAMPLES = SAMPLES;
    global.UDCF_FORMAT_TO_OPTION_KEY = formatToOptionKey;

    if (typeof SAMPLES.base64 === 'undefined') {
        try { global.UDCF_SAMPLES.base64 = btoa(unescape(encodeURIComponent(JSON.stringify({ name: 'John', age: 30 })))); } catch(e) { global.UDCF_SAMPLES.base64 = 'eyJuYW1lIjoiSm9obiIsImFnZSI6MzB9'; }
    }
})(typeof window !== 'undefined' ? window : this);
