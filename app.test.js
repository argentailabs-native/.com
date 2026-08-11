const test = require('node:test');
const assert = require('node:assert/strict');
const { findMatches } = require('./app.js');

test('filters groups by course and overlapping availability', () => {
  const matches = findMatches({ course: 'BIO 201', times: ['Tue afternoon'], style: 'Active discussion', format: 'In-person' });
  assert.deepEqual(matches.map(match => match.name), ['Bio Study Collective', 'Bio Focus Room']);
});

test('ranks compatible study style and format first', () => {
  const matches = findMatches({ course: 'BIO 201', times: ['Tue afternoon', 'Wed evening'], style: 'Active discussion', format: 'In-person' });
  assert.equal(matches[0].name, 'Bio Study Collective');
  assert.equal(matches[0].score, 99);
});

test('returns an empty list without an overlap', () => {
  assert.deepEqual(findMatches({ course: 'CHEM 101', times: ['Fri morning'], style: 'Quiet review', format: 'Virtual' }), []);
});
