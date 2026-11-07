"""Offline tests for the separate Loon direct-app subscription."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://raw.githubusercontent.com/zhangzhishan/apple-ai-rules/master/Loon-Direct.list'
APPLE_SHA = '6214f8b5e2e465290cb074cb0f7131c46efbc03214845a7cc5df269d54a66314'


def parse(text):
    rules = []
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        fields = line.split(',')
        if len(fields) != 2:
            raise ValueError('policy-free two-field rule required')
        kind, value = fields
        if kind not in ('DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'):
            raise ValueError('domain matches only')
        if kind == 'DOMAIN-KEYWORD':
            if value not in ('weibo', 'spotify'):
                raise ValueError('unreviewed keyword')
        elif len(value) > 253 or len(value.split('.')) < 2 or any(
            not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
            for label in value.split('.')
        ):
            raise ValueError('invalid domain')
        rules.append((kind, value))
    return rules


def matches(rule, host):
    kind, value = rule
    if kind == 'DOMAIN':
        return host == value
    if kind == 'DOMAIN-SUFFIX':
        return host == value or host.endswith('.' + value)
    return value in host


class LoonDirectRules(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / 'Loon-Direct.list').read_text()
        self.rules = parse(self.text)

    def test_complete_reviewed_snapshot(self):
        baseline = json.loads((ROOT / 'tests/fixtures/loon-direct-baseline.json').read_text())
        self.assertEqual([','.join(x) for x in self.rules], baseline['rules'])
        self.assertEqual(len(self.rules), len(set(self.rules)))

    def test_apple_ai_file_is_not_changed_or_mixed(self):
        self.assertEqual(hashlib.sha256((ROOT / 'Apple-AI.list').read_bytes()).hexdigest(), APPLE_SHA)
        for host in ('guzzoni.apple.com', 'smoot.apple.com', 'mask-api.icloud.com'):
            self.assertFalse(any(matches(rule, host) for rule in self.rules))

    def test_all_four_services_and_dependent_assets(self):
        hosts = ('restapi.amap.com', 'autonavi.com', 'a-map.cn',
                 'api.weibo.cn', 'passport.weibo.com', 'wx1.sinaimg.cn',
                 'sinajs.cn', 't.cn', 'api.m.jd.com', 'img10.360buyimg.com',
                 'jdpay.com', 'accounts.spotify.com', 'api.spotify.com',
                 'audio-fa.scdn.co', 'audio4-ak-spotify-com.akamaized.net',
                 'spotifycdn.net')
        for host in hosts:
            with self.subTest(host=host):
                self.assertTrue(any(matches(rule, host) for rule in self.rules))

    def test_unrelated_roots_and_shared_clouds_not_bypassed(self):
        for host in ('apple.com', 'icloud.com', 'google.com', 'github.com',
                     'openai.com', 'akamaized.net', 'amazonaws.com', 'cloudfront.net'):
            self.assertFalse(any(matches(rule, host) for rule in self.rules), host)
        self.assertTrue(all(rule[0] != 'IP-CIDR' for rule in self.rules))

    def test_exact_suffix_and_keyword_semantics(self):
        exact = ('DOMAIN', 'spotify.map.fastly.net')
        self.assertTrue(matches(exact, 'spotify.map.fastly.net'))
        self.assertFalse(matches(exact, 'x.spotify.map.fastly.net'))
        suffix = ('DOMAIN-SUFFIX', 'amap.com')
        self.assertTrue(matches(suffix, 'amap.com'))
        self.assertTrue(matches(suffix, 'restapi.amap.com'))
        self.assertFalse(matches(suffix, 'notamap.com'))
        self.assertFalse(matches(suffix, 'amap.com.example.org'))
        self.assertTrue(matches(('DOMAIN-KEYWORD', 'spotify'), 'spotify-example.net'))

    def test_invalid_or_policy_bearing_rules_rejected(self):
        for line in ('DOMAIN,spotify.com,DIRECT', 'DOMAIN-SUFFIX,*.jd.com',
                     'IP-CIDR,35.186.224.0/19', 'USER-AGENT,Spotify*',
                     'DOMAIN-KEYWORD,cloud', 'DOMAIN,APPLE.com',
                     'DOMAIN,https://amap.com', 'payload:'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse(line)

    def test_readme_uses_independent_url_and_direct_policy(self):
        readme = (ROOT / 'README.md').read_text()
        self.assertIn(URL + ',policy=DIRECT,tag=', readme)
        self.assertNotIn(URL + ',policy=Apple', readme)
        self.assertIn('Apple-AI.list', readme)
        self.assertIn('不是按 App/进程识别', readme)

    def test_plain_utf8_lf_and_sources(self):
        raw = (ROOT / 'Loon-Direct.list').read_bytes()
        self.assertTrue(raw.endswith(b'\n'))
        self.assertNotIn(b'\r', raw)
        self.assertTrue(self.text.startswith('#'))
        self.assertIn('blackmatrix7/ios_rule_script', self.text)
        self.assertFalse(any(re.search(r'password|token=|uuid=|subscription=', line, re.I)
                             for line in self.text.splitlines()))


if __name__ == '__main__':
    unittest.main()
