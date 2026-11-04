"""Offline contract tests for the shared Mihomo/Loon domain-only text file."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://raw.githubusercontent.com/zhangzhishan/apple-ai-rules/master/Apple-AI.list'
EXPECTED = {
    'guzzoni.apple.com', 'smoot.apple.com', 'api-siri-prod.apple.com',
    'seed.siri.apple.com', 'apple-relay.apple.com', 'apple-relay.cloudflare.com',
    'apple-relay.fastly-edge.com', 'cp4.cloudflare.com',
    'apple-relay.mask.apple-dns.net', 'mask-api.icloud.com',
    'mask-api.fe2.apple-dns.net', 'apple-relay.akamaized.net',
    'apple-carry-relay.cloudflare.com', 'gspe1-ssl.ls.apple.com',
    'gateway.icloud.com', 'probe.icloud.com', 'metrics.icloud.com', 'wps.apple.com',
}


def parse(text):
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        fields = line.split(',')
        if len(fields) != 2 or fields[0] not in ('DOMAIN', 'DOMAIN-SUFFIX'):
            raise ValueError(f'line {number}: expected domain-only, two-field rule')
        host = fields[1]
        if len(host) > 253 or not host.isascii() or host != host.lower():
            raise ValueError(f'line {number}: noncanonical domain')
        labels = host.split('.')
        if len(labels) < 2 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in labels):
            raise ValueError(f'line {number}: invalid domain')
        result.append((fields[0], host))
    return result


def matches(rule, hostname):
    kind, domain = rule
    return hostname == domain or (kind == 'DOMAIN-SUFFIX' and hostname.endswith('.' + domain))


class SharedRules(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / 'Apple-AI.list').read_text(encoding='utf-8')
        self.rules = parse(self.text)

    def test_requested_baseline_is_preserved_exactly(self):
        self.assertEqual({host for _, host in self.rules}, EXPECTED)
        self.assertEqual(len(self.rules), len(EXPECTED))

    def test_types_and_order_preserve_requested_semantics(self):
        self.assertEqual(self.rules[0], ('DOMAIN', 'guzzoni.apple.com'))
        self.assertEqual([x for x in self.rules if x[0] == 'DOMAIN-SUFFIX'], [('DOMAIN-SUFFIX', 'smoot.apple.com')])

    def test_no_duplicates_policies_yaml_or_wildcards(self):
        self.assertEqual(len(self.rules), len(set(self.rules)))
        self.assertNotIn('payload:', self.text)
        self.assertNotIn('rule-providers:', self.text)
        self.assertTrue(all('*' not in host for _, host in self.rules))

    def test_suffix_matches_only_label_boundary(self):
        rule = ('DOMAIN-SUFFIX', 'smoot.apple.com')
        for host in ('smoot.apple.com', 'x.smoot.apple.com'):
            self.assertTrue(matches(rule, host))
        for host in ('notsmoot.apple.com', 'smoot.apple.com.example.org', 'apple.com'):
            self.assertFalse(matches(rule, host))

    def test_exact_domain_does_not_expand(self):
        rule = ('DOMAIN', 'mask-api.fe2.apple-dns.net')
        self.assertTrue(matches(rule, 'mask-api.fe2.apple-dns.net'))
        self.assertFalse(matches(rule, 'mask-api.fe.apple-dns.net'))
        self.assertFalse(matches(rule, 'x.mask-api.fe2.apple-dns.net'))

    def test_invalid_or_policy_bearing_rules_are_rejected(self):
        for text in ('DOMAIN,apple.com,DIRECT', 'payload:', 'DOMAIN,*.apple.com',
                     'DOMAIN,apple.com # inline', 'DOMAIN,APPLE.com',
                     'DOMAIN,https://apple.com', 'DOMAIN,-bad.apple.com',
                     'SCRIPT,example.org', 'DOMAIN,apple..com'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse(text)

    def test_readme_and_mihomo_use_the_same_raw_url_and_format(self):
        readme = (ROOT / 'README.md').read_text()
        snippet = (ROOT / 'examples/mihomo-snippet.yaml').read_text()
        self.assertIn(URL, readme)
        self.assertIn('url: ' + URL, snippet)
        for expected in ('behavior: classical', 'format: text',
                         '- RULE-SET,apple-ai,Apple Intelligence US'):
            self.assertIn(expected, snippet)
        self.assertEqual(snippet.count('\nrule-providers:'), 1)
        self.assertEqual(snippet.count('\nrules:'), 1)

    def test_lf_comments_and_final_newline(self):
        raw = (ROOT / 'Apple-AI.list').read_bytes()
        self.assertNotIn(b'\r', raw)
        self.assertTrue(raw.endswith(b'\n'))
        self.assertFalse(any('DOMAIN,' in line for line in self.text.splitlines() if line.startswith('#')))


if __name__ == '__main__':
    unittest.main()
