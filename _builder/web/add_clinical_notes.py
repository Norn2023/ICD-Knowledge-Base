"""Add posterior circulation clinical notes to 8765 ICD app."""
import re

with open(r'D:\AI_libra\codex_Obsi\_builder\web\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove G45/I63 entries from _mccCrit (they were wrong place)
# Find _mccCrit start and end
mcc_start = content.find('var _mccCrit={')
mcc_end = content.find('\nfunction _mccCriteria', mcc_start)
mcc_block = content[mcc_start:mcc_end]

# Only remove lines with G45/I63/I65/G46 codes
lines = mcc_block.split('\n')
new_lines = []
for line in lines:
    if re.search(r"'G45\.|'I63\.|'I65\.|'G46\.", line):
        continue
    new_lines.append(line)
content = content[:mcc_start] + '\n'.join(new_lines) + content[mcc_end:]

# 2. Add _clinicalNotes object after _mccCrit
clinical = """
var _clinicalNotes={
'G45.000':{n:'椎基底动脉供血不足(后循环TIA)',s:'眩晕(47%)+复视+构音障碍+共济失调+双侧/交叉性感觉运动障碍+跌倒发作+TGA',i:'MRI+DWI(金标准,排除梗死);CTA/MRA;TCD',r:'后循环TIA:24h内症状完全恢复+DWI无梗死灶。孤立性眩晕极少是PCI,须合并其他脑干/小脑体征。ABCD²评分对后循环TIA预测价值有限,建议常规CTA/MRA。|参考文献:中国后循环缺血专家共识(2006);中国急性缺血性脑卒中诊治指南(2023);中国脑血管病临床管理指南(2023);NEJM后循环综述(2023)'},
'G45.001':{n:'椎动脉综合征(Wallenberg)',s:'眩晕+复视+同侧Horner+对侧痛温觉障碍+小脑性共济失调',i:'MRI+DWI;CTA/MRA示椎动脉狭窄/闭塞;DSA金标准',r:'同侧Horner+同侧面部痛温觉↓+对侧肢体痛温觉↓+眩晕/恶心/眼震+构音障碍/吞咽困难+同侧小脑共济失调。最常见病因:椎动脉夹层/动脉粥样硬化。|参考文献:后循环缺血专家共识(2006)'},
'G45.002':{n:'基底动脉综合征(基底动脉尖)',s:'意识障碍+四肢瘫+瞳孔异常+眼动障碍+去脑强直',i:'MRI+DWI;CTA/MRA示基底动脉狭窄/闭塞;DSA可同时介入',r:'基底动脉尖=双侧丘脑+中脑+枕叶+颞叶内侧→意识障碍/垂直凝视麻痹/皮质盲/Korsakoff样遗忘。基底动脉闭塞自然病程死亡率>80%,需积极再通。|参考文献:中国脑血管病临床管理指南(2023);NEJM后循环综述(2023)'},
'G45.900':{n:'短暂性脑缺血发作(后循环)',s:'眩晕+复视+构音障碍+共济失调+双侧/交叉性感觉运动障碍+视野缺损',i:'MRI+DWI(必须无梗死灶);CTA/MRA评估血管',r:'后循环TIA卒中复发风险与前循环无显著差异。双抗:轻型TIA(NIHSS≤3),24h内阿司匹林+氯吡格雷,21天后改单抗。鉴别:BPPV/梅尼埃病/前庭神经炎/前庭性偏头痛。|参考文献:中国急性缺血性脑卒中指南(2023)'},
'I63.900':{n:'脑梗死(急性缺血性脑卒中)',s:'突发局灶性神经功能缺损:偏瘫+偏身感觉障碍+偏盲+失语+构音障碍+眩晕/共济失调(后循环)',l:'血糖(排除低血糖)+凝血功能',i:'CT平扫(排除出血);MRI+DWI(金标准,敏感性>95%);CTA/MRA评估大血管闭塞',r:'急性期:①溶栓(阿替普酶0.9mg/kg,≤4.5h,后循环可延至6-9h);②取栓(大血管闭塞,≤24h);③双抗(轻型NIHSS≤3);④他汀强化。后循环梗死出血风险不高于前循环。|参考文献:中国急性缺血性脑卒中诊治指南(2023);中国脑血管病临床管理指南(2023)'},
'I65.001':{n:'椎动脉闭塞/狭窄',s:'眩晕+脑干/小脑缺血+TIA/卒中发作',l:'血脂+血糖+HbA1c',i:'CTA/MRA示椎动脉狭窄;DSA金标准',r:'动脉粥样硬化(45%)+夹层(年轻患者)。狭窄>50%有临床意义。治疗:抗血小板+他汀强化+危险因素控制。|参考文献:中国脑血管病临床管理指南(2023)'},
'I65.101':{n:'基底动脉闭塞/狭窄',s:'意识障碍+四肢瘫+瞳孔异常+眼动障碍+后循环TIA/卒中',l:'血脂+血糖+HbA1c',i:'CTA/MRA/DSA示基底动脉狭窄/闭塞',r:'基底动脉闭塞为最严重缺血性卒中类型,未经治疗死亡率>80%。|参考文献:中国脑血管病临床管理指南(2023)'},
'I63.901':{n:'脑干梗死',s:'复视+眩晕+构音障碍+吞咽困难+交叉性瘫+共济失调+Horner征',i:'MRI+DWI(必须,CT假阴性率高);CTA/MRA评估椎基底动脉',r:'脑干梗死症状复杂:延髓(Wallenberg)/脑桥(Millard-Gubler/Foville)/中脑(Weber/Benedikt)。后循环可适当延长溶栓时间窗。|参考文献:后循环缺血专家共识(2006)'},
'I63.902':{n:'小脑梗死',s:'眩晕+恶心呕吐+共济失调+眼球震颤+头痛',i:'MRI+DWI确诊;CT早期可正常',r:'小脑梗死占全部脑梗死3%。警惕:小脑水肿→梗阻性脑积水→脑干受压→枕骨大孔疝。大面积(>1/3小脑半球)→去骨瓣减压。|参考文献:中国脑血管病临床管理指南(2023)'},
'G46.300':{n:'小脑后下动脉综合征(Wallenberg)',s:'同侧Horner+同侧面部痛温觉↓+对侧肢体痛温觉↓+眩晕/恶心/眼震+构音障碍/吞咽困难+同侧小脑共济失调',i:'MRI+DWI示延髓背外侧梗死;CTA/MRA示椎动脉/PICA病变',r:'后循环梗死最常见类型(占36%)。最常见病因:椎动脉/PICA动脉粥样硬化/夹层。预后较好:多数恢复独立行走。|参考文献:后循环缺血专家共识(2006)'},
};
"""

# Insert before _mccCriteria function
insert_pos = content.find('\nfunction _mccCriteria')
content = content[:insert_pos] + clinical + content[insert_pos:]

# 3. Modify t10() to show clinical notes
old = "hc.innerHTML='<div style=\"padding:8px 16px;font-size:.75em;color:var(--text-dim)\">亚目:<b>'+h.su+'</b> '+h.sun+usp(h.sun)+'→ 类目:<b>'+h.ca+'</b> '+h.can+usp(h.can)+'→ 节:<b>'+h.se+'</b> '+h.sen+'→ <b style=\"color:var(--accent)\">第'+h.cno+'章</b>: '+h.chn+'</div>'"
new = """var cn=_clinicalNotes[code];var cH='';if(cn){cH='<div style=\"margin-top:6px;padding:8px 14px;background:#fefce8;border-radius:6px;border-left:4px solid var(--warning);font-size:.76em\"><b style=\"color:#92400e\">📋 '+cn.n+'</b>';if(cn.s)cH+='<div style=\"margin-top:3px\"><b>症状:</b> '+cn.s+'</div>';if(cn.l)cH+='<div><b>检验:</b> '+cn.l+'</div>';if(cn.i)cH+='<div><b>检查:</b> '+cn.i+'</div>';if(cn.r)cH+='<div style=\"margin-top:3px;color:var(--text-dim);font-size:.92em\"><b>指南/共识:</b> '+cn.r.replace(/\\|/g,'<br>')+'</div>';cH+='</div>'}hc.innerHTML='<div style=\"padding:8px 16px;font-size:.75em;color:var(--text-dim)\">亚目:<b>'+h.su+'</b> '+h.sun+usp(h.sun)+'→ 类目:<b>'+h.ca+'</b> '+h.can+usp(h.can)+'→ 节:<b>'+h.se+'</b> '+h.sen+'→ <b style=\"color:var(--accent)\">第'+h.cno+'章</b>: '+h.chn+'</div>'+cH"""

if old in content:
    content = content.replace(old, new)
    print('Modified t10() to show clinical notes')
else:
    print('WARNING: Could not find t10() code to modify!')

with open(r'D:\AI_libra\codex_Obsi\_builder\web\app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - added _clinicalNotes and updated t10()')
