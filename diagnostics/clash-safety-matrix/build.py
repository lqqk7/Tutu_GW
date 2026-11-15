#!/usr/bin/env python3
"""Public, synthetic-only compatibility fixtures; not production configuration."""
import copy
import json
from pathlib import Path
import subprocess
import yaml
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
BRANCH='codex/clash-safety-preview-20261115'
RAW='https://raw.githubusercontent.com/lqqk7/Tutu_GW/'
BASE_SHA='2ed3ecf'
def old(path):
    return subprocess.check_output(['git','show','c90dba9:'+path],cwd=ROOT,text=True)
preview_ini=(ROOT/'OC_Rules/Custom_Clash_Client.ini').read_text()
preview_ini=preview_ini.replace(RAW+BRANCH+'/', RAW+BASE_SHA+'/')
preview_base=yaml.safe_load((ROOT/'OC_Rules/Custom_Clash_Client_Base.yaml').read_text())
old_ini=old('OC_Rules/Custom_Clash_Client.ini').replace(RAW+'main/', RAW+'c90dba9/')
old_base=yaml.safe_load(old('OC_Rules/Custom_Clash_Client_Base.yaml'))
manual='custom_proxy_group=🚀 手动选择`select`(?i)^US-RELAY-.+$`[]REJECT'
poly='custom_proxy_group=Polymarket 国际站`select`(?i)^HK-.+$`[]REJECT'
CASES=[]
def add(name, base, ini, protected_native=True, no_inline=False, no_guards=False, direct_and=False, remote_safety=False):
    base=copy.deepcopy(base)
    base_path=f'diagnostics/clash-safety-matrix/base-{name}.yaml'
    base_url=RAW+BRANCH+'/'+base_path
    lines=ini.splitlines()
    lines=[('clash_rule_base='+base_url if line.startswith('clash_rule_base=') else line) for line in lines]
    if not protected_native:
        # Replace old declarations if present, otherwise add both concrete groups.
        lines=[line for line in lines if not line.startswith(('custom_proxy_group=🚀 手动选择`','custom_proxy_group=Polymarket 国际站`'))]
        lines.extend([manual, poly])
    if no_inline:
        lines=[line for line in lines if not line.startswith(('ruleset=REJECT,[]RULE-SET,Tutu_IPv6_Block','ruleset=REJECT,[]RULE-SET,Tutu_QUIC_Block'))]
    if no_guards:
        lines=[line for line in lines if not line.startswith('ruleset=REJECT,') or 'Tutu_' in line]
    if direct_and:
        lines=[line.replace('[]RULE-SET,Tutu_IPv6_Block','[]IP-CIDR6,::/0,no-resolve').replace('[]RULE-SET,Tutu_QUIC_Block','[]AND,((NETWORK,UDP),(DST-PORT,443))') for line in lines]
    if remote_safety:
        lines=[line.replace('[]RULE-SET,Tutu_IPv6_Block','clash-classic:'+RAW+BRANCH+'/diagnostics/clash-safety-matrix/IPv6_Classical.yaml,28800').replace('[]RULE-SET,Tutu_QUIC_Block','clash-classic:'+RAW+BRANCH+'/diagnostics/clash-safety-matrix/QUIC_Classical.yaml,28800') for line in lines]
    (ROOT/base_path).write_text(yaml.safe_dump(base,allow_unicode=True,sort_keys=False))
    (OUT/f'{name}.ini').write_text('\n'.join(lines)+'\n')
    CASES.append({'name':name,'ini':f'diagnostics/clash-safety-matrix/{name}.ini','base':base_path})

def without(base,*keys):
    value=copy.deepcopy(base)
    for key in keys:
        value.pop(key,None)
    return value

def seeded(base, value):
    value_base=copy.deepcopy(base)
    for group in value_base.get('proxy-groups',[]):
        group['proxies']=copy.deepcopy(value)
    return value_base

minimal={'mixed-port':7893,'allow-lan':False,'mode':'rule','log-level':'info','ipv6':True,
         'proxy-groups':copy.deepcopy(preview_base['proxy-groups'])}
minimal_ini='''[custom]
clash_rule_base=PLACEHOLDER
include_remarks=(?i)^(?:US-RELAY|HK)-.+$
ruleset=🚀 手动选择,[]FINAL
enable_rule_generator=true
overwrite_original_rules=true
'''
inline_min=without(minimal,'proxy-groups')
inline_min['rule-providers']=copy.deepcopy(preview_base['rule-providers'])
inline_ini=minimal_ini.replace('ruleset=🚀 手动选择,[]FINAL','ruleset=REJECT,[]RULE-SET,Tutu_IPv6_Block\nruleset=REJECT,[]RULE-SET,Tutu_QUIC_Block\nruleset=🚀 手动选择,[]FINAL')
add('control-old-branch-base',old_base,old_ini,protected_native=False)
add('native-min',minimal,minimal_ini)
add('native-empty-min',seeded(minimal,[]),minimal_ini)
add('native-static-reject-min',seeded(minimal,['REJECT']),minimal_ini)
add('inline-min',inline_min,inline_ini,protected_native=False)
add('full-current',preview_base,preview_ini)
add('full-native-empty',seeded(preview_base,[]),preview_ini)
add('full-no-native',without(preview_base,'proxy-groups'),preview_ini,protected_native=False)
add('full-no-inline',without(preview_base,'rule-providers'),preview_ini,no_inline=True)
add('full-no-inline-native-empty',seeded(without(preview_base,'rule-providers'),[]),preview_ini,no_inline=True)
add('full-no-guards',preview_base,preview_ini,no_guards=True)
add('full-no-native-no-inline',without(preview_base,'proxy-groups','rule-providers'),preview_ini,protected_native=False,no_inline=True)
add('full-new-tun-only',without(preview_base,'proxy-groups','rule-providers'),preview_ini,protected_native=False,no_inline=True,no_guards=True)
add('full-remote-safety-native-empty',seeded(without(preview_base,'rule-providers'),[]),preview_ini,remote_safety=True)
add('full-direct-and-native-empty',seeded(without(preview_base,'rule-providers'),[]),preview_ini,direct_and=True)
(OUT/'IPv6_Classical.yaml').write_text('payload:\n  - IP-CIDR6,::/0,no-resolve\n')
(OUT/'QUIC_Classical.yaml').write_text('payload:\n  - AND,((NETWORK,UDP),(DST-PORT,443))\n')
(OUT/'cases.json').write_text(json.dumps(CASES,ensure_ascii=False,indent=2)+'\n')
(OUT/'README.md').write_text('# Clash 转换兼容性隔离矩阵\n\n只包含公开规则、配置与无鉴权的合成节点名称，不用于生产。测试请求在本地构造；任何用户订阅、真实节点凭据都不得加入本目录。\n\n`build.py` 基于预览配置生成独立变体，`cases.json` 记录变量范围。\n')
print(len(CASES))
