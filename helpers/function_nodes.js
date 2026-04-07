/**
 * n8n Function node snippets for Argent AI Labs social workflow
 */

// 1) Build deterministic fingerprint to avoid duplicates
function buildFingerprint(topic, angle, hook, platform) {
  const crypto = require('crypto');
  const raw = `${(topic||'').toLowerCase()}|${(angle||'').toLowerCase()}|${(hook||'').toLowerCase()}|${(platform||'').toLowerCase()}`;
  return crypto.createHash('sha256').update(raw).digest('hex');
}

// 2) Validate AI JSON safety
function safeParseLLM(content) {
  try {
    return JSON.parse(content);
  } catch (err) {
    return {
      _parse_error: true,
      message: err.message,
      raw: content
    };
  }
}

// 3) Determine whether to regenerate hooks
function needsRegeneration(qa) {
  const floor = 75;
  const keys = ['instagram', 'x', 'facebook'];
  for (const k of keys) {
    const p = qa?.scores?.[k] || {};
    const values = [p.hook_strength, p.specificity, p.human_naturalness, p.non_repetitiveness, p.business_value];
    if (values.some(v => Number(v) < floor)) return true;
  }
  return false;
}

module.exports = { buildFingerprint, safeParseLLM, needsRegeneration };
