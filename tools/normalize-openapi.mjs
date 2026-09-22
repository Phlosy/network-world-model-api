import { readFileSync, writeFileSync } from 'node:fs';

const inputPath = '/home/xpk/workspace/network-world-state-openapi-0.1.json';
const outputPath = '/home/xpk/workspace/network-world-model-api/contracts/openapi/network-world-state.openapi.json';

const raw = readFileSync(inputPath, 'utf8');
const spec = JSON.parse(raw);

function transformTo303(obj) {
  if (Array.isArray(obj)) {
    return obj.map(transformTo303);
  } else if (obj !== null && typeof obj === 'object') {
    // Handle oneOf / anyOf with null
    if ((obj.oneOf || obj.anyOf) && Array.isArray(obj.oneOf || obj.anyOf)) {
      const list = obj.oneOf || obj.anyOf;
      const nullIndex = list.findIndex(item => item && item.type === 'null');
      if (nullIndex !== -1 && list.length === 2) {
        const other = list[1 - nullIndex];
        const res = transformTo303(other);
        res.nullable = true;
        if (obj.description && !res.description) {
          res.description = obj.description;
        }
        return res;
      }
    }

    const res = {};
    for (const [k, v] of Object.entries(obj)) {
      if (k === 'type' && Array.isArray(v)) {
        if (v.length === 2 && v.includes('null')) {
          const nonNull = v.find(t => t !== 'null');
          res['type'] = nonNull;
          res['nullable'] = true;
        } else if (v.length === 1) {
          res['type'] = v[0];
        } else {
          res['type'] = v;
        }
      } else if (k === 'const') {
        res['enum'] = [v];
      } else if (k === 'examples' && Array.isArray(v)) {
        // In OpenAPI 3.0 Schema Object, field is 'example' rather than 'examples'
        res['example'] = v.length === 1 ? transformTo303(v[0]) : transformTo303(v);
      } else {
        res[k] = transformTo303(v);
      }
    }
    return res;
  }
  return obj;
}

const contract = transformTo303(spec);
contract.openapi = '3.0.3';
delete contract.jsonSchemaDialect;
contract.servers = [
  {
    url: 'https://api.network-world-model.local',
    description: 'Default environment',
  },
];

writeFileSync(outputPath, JSON.stringify(contract, null, 2) + '\n', 'utf8');
console.log(`Successfully generated standardized OpenAPI 3.0.3 contract at ${outputPath}`);
