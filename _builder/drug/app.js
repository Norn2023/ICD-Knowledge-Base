var D=null;
var _dl=document.getElementById('load');
var _pharm=null;
var _clin=null;

var _loaded=0;
function _checkReady(){
    _loaded++;
    if(_loaded>=3){_rdy();}
}
setTimeout(function(){if(_loaded<3){_loaded=3;_rdy();}},8000);

fetch('drugs.json').then(function(r){
    if(!r.ok) throw new Error('HTTP '+r.status);
    return r.json();
}).then(function(d){
    D=d;_checkReady();
}).catch(function(e){
    _dl.innerHTML='<div class="emp"><p>数据加载失败: '+e.message+'<br><small>请按 Ctrl+F5 强制刷新</small></p></div>';
});
fetch('pharmacopoeia_index.json').then(function(r){return r.json()}).then(function(d){
    _pharm=d;_checkReady();
}).catch(function(e){_pharm=[];_checkReady();});
fetch('clinical_ref_index.json').then(function(r){return r.json()}).then(function(d){
    _clin=d;_checkReady();
}).catch(function(e){_clin={};_checkReady();});

function _rdy(){
    _dl.style.display='none';
    document.querySelector('main').style.display='block';
    if(D){sd();}else{document.getElementById('drug-tb').innerHTML='<tr><td colspan="7" class="emp">数据加载失败，请刷新页面</td></tr>';}
}

// Tab switching
function st(n){
    document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});
    document.querySelectorAll('nav button').forEach(function(b){b.classList.remove('active')});
    var t=document.getElementById('t-'+n);
    if(t)t.classList.add('active');
    document.querySelectorAll('nav button').forEach(function(b,i){
        if((n==='catalog'&&i===0))b.classList.add('active');
    });
    if(n==='pharm')_pharmSearch();
    if(n==='rules')_loadRules();
}

// === DRUG CATALOG ===
function sd(){
    if(!D){document.getElementById('drug-tb').innerHTML='<tr><td colspan="7" class="emp">加载中...</td></tr>';return}
    var q=document.getElementById('qd').value||'';
    console.log('sd() called, q="'+q+'", D.len='+D.length);
    var r=D;
    if(q.trim()){
        var ql=q.trim();
        r=D.filter(function(d){
            if((d.name||'').indexOf(ql)>=0)return true;
            if((d.code||'').indexOf(ql)>=0)return true;
            if((d.cat||'').indexOf(ql)>=0)return true;
            if((d.form||'').indexOf(ql)>=0)return true;
            if((d.note||'').indexOf(ql)>=0)return true;
            return false;
        });
    }
    var total=r.length,show=r.slice(0,100);
    var catalog2025=D.filter(function(d){return !d._source||d._source!=='2026医保分类'}).length;
    var src2026=D.filter(function(d){return d._source==='2026医保分类'}).length;
    document.getElementById('drug-info').textContent=q.trim()?'搜索匹配 '+total+' 条药品':'共 '+D.length.toLocaleString()+' 条药品（2025目录·'+catalog2025+' + 2026新增·'+src2026+'）';

    document.getElementById('drug-th').innerHTML='<tr><th style="width:6%">类型</th><th style="width:8%">分类编码</th><th style="width:16%">分类</th><th style="width:18%">药品名称</th><th style="width:8%">剂型</th><th style="width:4%">级别</th><th style="width:28%">医保备注</th></tr>';

    document.getElementById('drug-tb').innerHTML=show.map(function(d,i){
        var typeTag=d.type==='西药'?'tag-s':'tag-a';
        var catFull=(d.cat||'')+(d.subcat?' › '+d.subcat:'')+(d.subsubcat?' › '+d.subsubcat:'');
        var origIdx=D.indexOf(d);
        var h='<tr onclick="_showDetail('+origIdx+')" title="点击查看详情">';
        h+='<td><span class="tag '+typeTag+'">'+d.type+'</span></td>';
        h+='<td><span class="tag" style="font-family:monospace;font-size:.78em">'+(d.code||'—')+'</span></td>';
        h+='<td style="font-size:.75em;line-height:1.4">'+catFull+'</td>';
        var dtags='';
        if(d.essential)dtags+=' <span class="tag tag-s" style="font-size:.6em;padding:1px 5px">基药</span>';
        if(d.disease_type==='慢病')dtags+=' <span class="tag tag-s" style="font-size:.6em;padding:1px 5px;background:var(--warning);color:#fff">慢病</span>';
        else if(d.disease_type==='特病')dtags+=' <span class="tag tag-s" style="font-size:.6em;padding:1px 5px;background:var(--danger);color:#fff">特病</span>';
        else if(d.disease_type==='慢病+特病')dtags+=' <span class="tag tag-s" style="font-size:.6em;padding:1px 5px;background:var(--danger);color:#fff">慢病+特病</span>';
        if(d.psychotropic_2)dtags+=' <span class="tag" style="font-size:.6em;padding:1px 5px;background:var(--danger);color:#fff">精二</span>';
        if(d.tags&&d.tags.length){d.tags.forEach(function(t){if(t.indexOf('大病')===0)dtags+=' <span class="tag" style="font-size:.6em;padding:1px 5px;background:#991b1b;color:#fef3c7" title="上海大病:'+t+'">🏥'+t.replace('大病-','')+'</span>';})};
        if(d._in_rx)dtags+=' <span class="tag tag-a" style="font-size:.6em;padding:1px 5px">📖处方集</span>';
        if(d.negotiated)dtags+=' <span class="tag" style="font-size:.6em;padding:1px 5px;background:#e11d48;color:#fff">国谈</span>';
        if(d._source==='2026医保分类')dtags+=' <span class="tag" style="font-size:.6em;padding:1px 5px;background:var(--accent);color:#fff">2026新增</span>';
        if(!d._has_variants)dtags+=' <span class="tag tag-w" style="font-size:.6em;padding:1px 5px">🟡无产品</span>';
        h+='<td style="font-weight:500">'+d.name+dtags+'</td>';
        h+='<td style="font-size:.82em">'+(d.form||'—')+'</td>';
        h+='<td><span class="tag '+(d.level==='甲'?'tag-s':'tag-w')+'">'+(d.level||'—')+'</span></td>';
        h+='<td style="font-size:.75em;color:var(--text-dim)">'+(d.note||'—')+'</td>';
        h+='</tr>';
        return h;
    }).join('');
}

// === DRUG DETAIL ===
function _showDetail(idx){
    if(!D||idx>=D.length)return;
    var d=D[idx];
    st('detail');
    document.getElementById('t-detail').querySelector('.emp').style.display='none';
    var h='<button onclick="st(\'catalog\')" style="margin-bottom:12px;padding:6px 14px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--bg-card);cursor:pointer;font-size:.85em">← 返回目录</button>';
    h+='<div class="detail-card">';
    var tags='';
    if(d.essential)tags+=' <span class="tag tag-s" style="font-size:.65em;vertical-align:middle">基药</span>';
    if(d.disease_type==='慢病')tags+=' <span class="tag tag-s" style="font-size:.65em;vertical-align:middle;background:var(--warning);color:#fff">慢病</span>';
    else if(d.disease_type==='特病')tags+=' <span class="tag tag-s" style="font-size:.65em;vertical-align:middle;background:var(--danger);color:#fff">特病</span>';
    else if(d.disease_type==='慢病+特病')tags+=' <span class="tag tag-s" style="font-size:.65em;vertical-align:middle;background:var(--danger);color:#fff">慢病+特病</span>';
    if(d.psychotropic_2)tags+=' <span class="tag" style="font-size:.65em;vertical-align:middle;background:var(--danger);color:#fff">精二</span>';
    if(d.negotiated)tags+=' <span class="tag" style="font-size:.65em;vertical-align:middle;background:#e11d48;color:#fff">国谈</span>';
    if(d.tags&&d.tags.length){d.tags.forEach(function(t){if(t.indexOf('大病')===0)tags+=' <span class="tag" style="font-size:.65em;vertical-align:middle;background:#991b1b;color:#fef3c7" title="上海大病:'+t+'">🏥'+t.replace('大病-','')+'</span>';})};
    if(d._source==='2026医保分类')tags+=' <span class="tag" style="font-size:.65em;vertical-align:middle;background:var(--accent);color:#fff">2026新增</span>';
    if(d._in_rx)tags+=' <span class="tag tag-a" style="font-size:.65em;vertical-align:middle">📖处方集</span>';
    if(!d._has_variants)tags+=' <span class="tag tag-w" style="font-size:.65em;vertical-align:middle">🟡无产品明细</span>';
    h+='<h3>'+d.name+tags+'</h3>';
    h+='<div class="detail-grid">';
    h+='<span class="label">类型</span><span class="value"><span class="tag tag-a">'+d.type+'</span></span>';
    h+='<span class="label">医保级别</span><span class="value"><span class="tag '+(d.level==='甲'?'tag-s':'tag-w')+'">'+d.level+'类</span></span>';
    h+='<span class="label">分类代码</span><span class="value"><code style="font-size:.9em">'+(d.code||'—')+'</code></span>';
    h+='<span class="label">药品分类</span><span class="value" style="font-size:.82em">'+(d.cat||'—')+(d.subcat?' › '+d.subcat:'')+(d.subsubcat?' › '+d.subsubcat:'')+'</span>';
    h+='<span class="label">剂型</span><span class="value">'+(d.form||'—')+'</span>';
    if(d.negotiated){
        var ni=d.nego_info||{};
        h+='<span class="label">国谈信息</span><span class="value" style="font-size:.8em">';
        h+='<span class="tag" style="background:#e11d48;color:#fff;font-size:.8em">国谈药品</span> ';
        if(ni.period)h+=ni.period+' ';
        if(ni.note)h+='<br><span style="font-size:.78em;color:var(--text-dim)">'+ni.note+'</span>';
        h+='</span>';
    }
    h+='</div>';
    if(d.note){
        h+='<div style="margin-top:16px;padding:12px;background:var(--warning-light);border-radius:var(--r);border-left:4px solid var(--warning)">';
        h+='<b style="font-size:.88em">📋 医保备注</b>';
        h+='<p style="margin-top:6px;font-size:.85em">'+d.note+'</p>';
        h+='</div>';
    }
    if(d._payment_change){
        var pc=d._payment_change;
        var pcType=pc.type||'';
        var pcColor=pcType==='新增限定'?'var(--danger)':(pcType==='解除限定'?'var(--success)':'var(--warning)');
        var pcIcon=pcType==='新增限定'?'🔴':(pcType==='解除限定'?'🟢':'🟡');
        h+='<div style="margin-top:8px;padding:10px 14px;background:#fefce8;border-radius:var(--r);border-left:4px solid '+pcColor+'">';
        h+='<b style="font-size:.85em">'+pcIcon+' 2024→2025 限定规则变化: '+pcType+'</b>';
        if(pc.v2024)h+='<div style="margin-top:4px;font-size:.78em"><b>2024版:</b> <span style="color:var(--text-dim)">'+_trunc(pc.v2024,150)+'</span></div>';
        if(pc.v2025)h+='<div style="margin-top:2px;font-size:.78em"><b>2025版:</b> <span style="color:var(--text)">'+_trunc(pc.v2025,150)+'</span></div>';
        h+='</div>';
    }

    // Pharmacopoeia reference
    if(_pharm){
        var pmatches=_pharm.filter(function(p){
            if(p.name===d.name) return true;
            var minLen=Math.min(p.name.length, d.name.length);
            if(minLen<4) return false;
            return (d.name&&p.name.indexOf(d.name)>=0) || (p.name&&d.name.indexOf(p.name)>=0);
        });
        if(pmatches.length>0){
            h+='<div style="margin-top:12px;padding:10px 14px;background:var(--accent-light);border-radius:var(--r);font-size:.85em">';
            h+='<b>📖 药典收录</b>: ';
            pmatches.slice(0,3).forEach(function(pm,i){
                if(i>0)h+='<br> ';
                h+=pm.name+' → '+pm.volume+' 第'+pm.page+'页 ';
                h+='<a href="/pdf?id='+pm.fid+'#page='+pm.page+'" target="_blank" style="font-size:.8em;color:var(--accent);text-decoration:none">[打开PDF]</a> ';
                h+='<span style="cursor:pointer;font-size:.8em;color:var(--success)" onclick="_previewPage(\''+pm.fid+'\','+pm.page+',this)">[预览]</span>';
            });
            h+='</div>';
        }
    }

    // Clinical reference
    if(_clin&&_clin.chem){
        var cmatches=_clin.chem.filter(function(c){
            var cn=c.name||'';
            if(cn===d.name) return true;
            // Substring match: require shorter name to be at least 4 chars to avoid false positives
            var minLen=Math.min(cn.length, d.name.length);
            if(minLen<4) return false;
            return (d.name&&cn.indexOf(d.name)>=0) || (cn&&d.name.indexOf(cn)>=0);
        });
        if(cmatches.length>0){
            h+='<div style="margin-top:8px;padding:10px 14px;background:var(--success-light);border-radius:var(--r);font-size:.85em">';
            h+='<b>📖 临床用药须知</b>（化学药卷）: ';
            cmatches.slice(0,3).forEach(function(cm,i){
                if(i>0)h+='<br> ';
                h+=cm.name+' → 第'+cm.page+'页 ';
                h+='<a href="/pdf?id='+cm.fid+'#page='+cm.page+'" target="_blank" style="font-size:.8em;color:var(--accent);text-decoration:none">[打开PDF]</a> ';
                h+='<span style="cursor:pointer;font-size:.8em;color:var(--success)" onclick="_previewPage(\''+cm.fid+'\','+cm.page+',this)">[预览]</span>';
            });
            h+='</div>';
        }
    }

    // National Formulary (国家处方集)
    if(_clin&&_clin.rx){
        var rmatches=_clin.rx.filter(function(r){
            var rn=r.name||'';
            if(rn===d.name) return true;
            var minLen=Math.min(rn.length, d.name.length);
            if(minLen<4) return false;
            return (d.name&&rn.indexOf(d.name)>=0) || (rn&&d.name.indexOf(rn)>=0);
        });
        if(rmatches.length>0){
            h+='<div style="margin-top:8px;padding:10px 14px;background:var(--warning-light);border-radius:var(--r);font-size:.85em">';
            h+='<b>📖 国家处方集收录</b>（2020版）: ';
            rmatches.slice(0,5).forEach(function(rm,i){
                if(i>0)h+='<br> ';
                h+=rm.name+' → 第'+rm.page+'页 ';
                h+='<a href="/pdf?id='+rm.fid+'#page='+rm.page+'" target="_blank" style="font-size:.8em;color:var(--accent);text-decoration:none">[打开PDF]</a> ';
                h+='<span style="cursor:pointer;font-size:.8em;color:var(--success)" onclick="_previewPage(\''+rm.fid+'\','+rm.page+',this)">[预览]</span>';
            });
            if(rmatches.length>5)h+='<br> <span style="font-size:.72em;color:var(--text-dim)">... 共'+rmatches.length+'处</span>';
            h+='</div>';
        }
    }
    h+='</div>';

    // Prescribing info section
    var rx=d.prescribing;
    if(rx){
        h+='<div class="detail-card" style="border-left:4px solid var(--accent)">';
        h+='<h4>药品说明书 <span style="font-weight:400;font-size:.78em;color:var(--text-dim)">'+rx.en_name+' | '+rx.category+'</span></h4>';

        // 1. 药品适应症 (ICD-10编码表)
        if(rx.indications&&rx.indications.length){
            h+='<div style="margin:16px 0"><b>1. 药品适应症</b> <span style="font-size:.72em;color:var(--text-dim)">ICD-10编码表</span>';
            h+='<div style="overflow-x:auto;margin:8px 0">';
            h+='<table style="font-size:.82em;min-width:780px"><thead><tr>';
            h+='<th style="width:4%">#</th><th style="width:34%">适应症</th><th style="width:12%">ICD-10编码</th>';
            h+='<th style="width:14%">疾病诊断</th><th style="width:14%">疾病分类</th><th style="width:22%">备注</th>';
            h+='</tr></thead><tbody>';
            rx.indications.forEach(function(ind,i){
                var txt=ind.text||ind.disease||'';
                var icd=ind.icd10||'—';
                // Build disease diagnosis name from available fields
                var diagName='';
                if(ind.慢病&&ind.慢病名称) diagName=ind.慢病名称;
                else if(ind.特病&&ind.特病名称) diagName=ind.特病名称;
                else if(ind.diagnosis) diagName=ind.diagnosis;
                if(!diagName){
                    // Try to infer from ICD-10 code
                    var icdMap={'E11.900':'2型糖尿病','E10.900':'1型糖尿病','E14.900':'糖尿病',
                        'E11.401':'糖尿病周围神经病变','E11.201':'糖尿病肾病',
                        'R73.000':'糖耐量异常','E66.900':'肥胖症','E78.500':'高脂血症',
                        'E78.000':'高胆固醇血症','E28.200':'多囊卵巢综合征',
                        'I10.x00':'原发性高血压','I25.101':'冠心病','I20.801':'稳定性心绞痛',
                        'I20.101':'变异型心绞痛','I50.900':'心力衰竭',
                        'K21.900':'胃食管反流病','K27.900':'消化性溃疡','K25.900':'胃溃疡',
                        'K26.900':'十二指肠溃疡','B98.000':'幽门螺杆菌感染',
                        'J45.900':'支气管哮喘','J44.900':'慢性阻塞性肺疾病',
                        'J02.900':'急性咽炎','J03.900':'急性扁桃体炎','J15.900':'细菌性肺炎',
                        'H66.900':'中耳炎','A49.900':'细菌感染','N39.000':'泌尿道感染',
                        'L08.900':'皮肤软组织感染','A54.900':'急性淋病','B49.x00':'真菌感染',
                        'A53.900':'梅毒','A27.900':'钩端螺旋体病',
                        'G40.900':'癫痫','G20.x00':'帕金森病',
                        'F00.900':'阿尔茨海默病','F01.900':'血管性痴呆','F03.x00':'痴呆',
                        'F32.900':'抑郁症','F20.900':'精神分裂症',
                        'C80.x00':'恶性肿瘤','N18.900':'慢性肾病',
                        'M06.900':'类风湿关节炎','M19.900':'骨关节炎','M45.x00':'强直性脊柱炎',
                        'R11.x00':'恶心呕吐','R52.900':'疼痛','R52.100':'癌性疼痛',
                        'R50.900':'发热','N91.000':'闭经','N93.801':'功能性子宫出血',
                        'O20.000':'先兆流产','E16.400':'卓-艾综合征',
                        'J30.400':'过敏性鼻炎','L50.900':'荨麻疹',
                        'K64.900':'痔','K64.801':'混合痔','I84.900':'外痔',
                        'K60.200':'肛裂','K62.800':'直肠炎/肛窦炎','K92.200':'便血',
                        'L30.900':'皮炎/湿疹','T30.000':'烧烫伤',
                        'J06.900':'急性上呼吸道感染','J20.900':'急性支气管炎',
                        'J31.200':'慢性咽炎','R05.x00':'咳嗽',
                        'H81.001':'梅尼埃病','R42.x00':'眩晕','G45.000':'椎基底动脉供血不足',
                        'I67.800':'慢性脑缺血','H91.200':'突发性耳聋',
                        'F31.900':'双相情感障碍','F33.200':'复发性抑郁障碍','F41.200':'混合性焦虑抑郁障碍',
                        'H10.900':'细菌性结膜炎','H16.900':'细菌性角膜炎','H01.000':'睑缘炎',
                        'Z48.800':'术后眼部炎症','H10.100':'过敏性结膜炎','A71.900':'沙眼','H00.000':'麦粒肿',
                        'T78.400':'过敏反应',
                        'I63.900':'急性缺血性脑卒中','G45.900':'短暂性脑缺血发作','I69.300':'脑卒中后遗症',
                        'E46.x00':'营养不良','K63.800':'肠功能障碍',
                        'Z94.800':'器官移植术后','E88.000':'低蛋白血症','K74.600':'肝硬化腹水',
                        'D70.x00':'中性粒细胞减少','B96.500':'铜绿假单胞菌感染','A41.900':'脓毒症',
                        'K83.100':'胆汁淤积性肝病','G93.600':'脑水肿','K59.000':'便秘',
                        'Z51.400':'结肠镜检查准备','O24.400':'妊娠期糖尿病','G00.900':'细菌性脑膜炎',
                        'K80.200':'胆囊胆固醇结石','K74.300':'原发性胆汁性胆管炎','K29.600':'胆汁反流性胃炎',
                        'T31.000':'大面积烧伤','Z51.800':'血浆置换','K65.000':'自发性细菌性腹膜炎',
                        'N04.900':'肾病综合征','M32.100':'系统性红斑狼疮','K56.400':'粪便嵌塞'};
                    diagName=icdMap[icd]||'';
                }
                var noteParts=[];
                var diseaseTag='';
                if(ind.慢病){
                    diseaseTag='<span class="tag tag-s" style="font-size:.72em">🟠 慢病';
                    if(ind.慢病名称) diseaseTag+=' · '+_trunc(ind.慢病名称,10);
                    diseaseTag+='</span>';
                }
                if(ind.特病){
                    diseaseTag+=(diseaseTag?' ':'')+'<span class="tag" style="font-size:.72em;background:var(--danger);color:#fff">🔴 特病';
                    if(ind.特病名称) diseaseTag+=' · '+_trunc(ind.特病名称,10);
                    diseaseTag+='</span>';
                }
                if(!diseaseTag) diseaseTag='<span style="font-size:.72em;color:var(--text-dim)">—</span>';
                if(ind.offlabel){
                    noteParts.push('<span class="tag tag-d" style="font-size:.7em">⚠ 超说明书</span>');
                    if(ind.offlabel_source) noteParts.push('<span style="font-size:.7em;color:var(--text-dim)">'+ind.offlabel_source+'</span>');
                }else{
                    noteParts.push('<span style="font-size:.72em;color:var(--success)">✔ 说明书内</span>');
                }
                var rowBg=ind.offlabel?'background:#fffbf0':(ind.特病?'background:#fff5f5':(ind.慢病?'background:#f0fdf4':''));
                h+='<tr style="'+rowBg+'">';
                h+='<td style="text-align:center;color:var(--text-dim)">'+(i+1)+'</td>';
                h+='<td style="line-height:1.55;font-size:.82em">'+txt+'</td>';
                h+='<td><code style="font-size:.82em;font-weight:600;color:var(--accent)">'+icd+'</code></td>';
                h+='<td style="font-size:.82em;font-weight:500;color:var(--text)">'+(diagName||'—')+'</td>';
                h+='<td>'+diseaseTag+'</td>';
                h+='<td>'+noteParts.join('<br>')+'</td>';
                h+='</tr>';
            });
            h+='</tbody></table></div>';
            h+='</div>';
        }

        // 2. 药品用法用量
        if(rx.dosage&&rx.dosage.length){
            h+='<div style="margin:16px 0"><b>2. 药品用法用量</b><ul style="font-size:.82em;margin:4px 0 0 16px">';
            rx.dosage.forEach(function(ds){
                var isMax=ds.indexOf('最大')>=0||ds.indexOf('上限')>=0;
                h+='<li'+(isMax?' style="color:var(--danger);font-weight:500"':'')+'>'+ds+'</li>';
            });
            h+='</ul></div>';
        }

        // 3. 药品不良反应
        if(rx.adverse_reactions&&rx.adverse_reactions.length){
            h+='<div style="margin:16px 0"><b>3. 药品不良反应</b><ul style="font-size:.82em;margin:4px 0 0 16px">';
            rx.adverse_reactions.forEach(function(a){h+='<li>'+a+'</li>';});
            h+='</ul></div>';
        }

        // 4. 药品禁忌症
        if(rx.contraindications&&rx.contraindications.length){
            h+='<div style="margin:16px 0;padding:10px 14px;background:#fff5f5;border-radius:var(--r);border-left:3px solid var(--danger)">';
            h+='<b style="color:var(--danger)">4. 药品禁忌症</b><ul style="font-size:.82em;margin:4px 0 0 16px">';
            rx.contraindications.forEach(function(c){h+='<li>'+c+'</li>';});
            h+='</ul></div>';
        }

        // 5. 药物配伍禁忌
        if(rx.interactions&&rx.interactions.length){
            h+='<div style="margin:16px 0;padding:10px 14px;background:var(--warning-light);border-radius:var(--r);border-left:3px solid var(--warning)">';
            h+='<b>5. 药物配伍禁忌/相互作用</b><ul style="font-size:.82em;margin:4px 0 0 16px">';
            rx.interactions.forEach(function(di){h+='<li>'+di+'</li>';});
            h+='</ul></div>';
        }

        // 6. 特殊人群用药
        if(rx.special_populations&&rx.special_populations.length){
            h+='<div style="margin:16px 0"><b>6. 特殊人群用药</b><ul style="font-size:.82em;margin:4px 0 0 16px">';
            rx.special_populations.forEach(function(sp){h+='<li>'+sp+'</li>';});
            h+='</ul></div>';
        }

        // 7. 其他
        if(rx.other&&rx.other.length){
            h+='<div style="margin:16px 0"><b>7. 其他</b><ul style="font-size:.82em;margin:4px 0 0 16px">';
            rx.other.forEach(function(o){h+='<li>'+o+'</li>';});
            h+='</ul></div>';
        }

        // 8. 医保审核注意事项
        if(rx.insurance_notes&&rx.insurance_notes.length){
            // Sort: high > medium > low (explicit 3-bucket sort)
            var riskOrder={high:0,medium:1,low:2};
            var high=[], medium=[], low=[], unknown=[];
            rx.insurance_notes.forEach(function(n){
                var r=(n.risk||'').toString().toLowerCase().trim();
                if(r==='high') high.push(n);
                else if(r==='medium') medium.push(n);
                else if(r==='low') low.push(n);
                else unknown.push(n);
            });
            var notes=high.concat(medium).concat(low).concat(unknown);
            h+='<div style="margin-top:16px;padding:12px 14px;background:var(--bg-input);border-radius:var(--r);border:1px solid var(--border)">';
            h+='<b style="color:var(--accent)">8. 医保审核注意事项</b> <span style="font-size:.72em;color:var(--text-dim)">'
                +'🔴'+high.length+'条高风险 · 🟡'+medium.length+'条中风险 · 🟢'+low.length+'条低风险</span>';
            h+='<div style="margin-top:8px">';
            notes.forEach(function(n,i){
                var risk=n.risk||'low';
                var riskBadge='';
                var borderColor='var(--text-dim)';
                if(risk==='high'){
                    riskBadge='<span class="tag" style="background:var(--danger);color:#fff;font-size:.7em;font-weight:700">🔴 高风险</span>';
                    borderColor='var(--danger)';
                }else if(risk==='medium'){
                    riskBadge='<span class="tag" style="background:var(--warning);color:#fff;font-size:.7em;font-weight:700">🟡 中风险</span>';
                    borderColor='var(--warning)';
                }else{
                    riskBadge='<span class="tag tag-s" style="font-size:.7em">🟢 低风险</span>';
                    borderColor='var(--success)';
                }
                var txt=typeof n==='string'?n:(n.text||'');
                var materials=n.materials||[];
                h+='<div style="margin:6px 0;padding:8px 12px;background:var(--bg-card);border-radius:var(--r-sm);border-left:4px solid '+borderColor+'">';
                h+='<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:4px">';
                h+=riskBadge;
                h+='<span style="font-size:.82em;line-height:1.5;flex:1">'+txt+'</span>';
                h+='</div>';
                if(materials.length){
                    h+='<div style="margin-top:6px;padding:6px 10px;background:var(--bg-input);border-radius:var(--r-sm)">';
                    h+='<span style="font-size:.7em;color:var(--text-dim);font-weight:600">📋 审核所需材料：</span>';
                    h+='<ul style="margin:3px 0 0 14px;font-size:.72em;color:var(--text-dim);padding-left:0;list-style:disc">';
                    materials.forEach(function(m){
                        h+='<li style="padding:1px 0">'+m+'</li>';
                    });
                    h+='</ul></div>';
                }
                h+='</div>';
            });
            h+='</div>';
            h+='<div style="margin-top:8px;font-size:.7em;color:var(--text-dim)">💡 按违规风险由高到低排列。审核材料为医保智能审核系统自动抓取所需的参考清单。</div>';
            h+='</div>';
        }

        h+='</div>';
    }

    // Variants table with click-to-expand detail
    var variants=d.variants||[];
    h+='<div class="detail-card">';
    h+='<h4>📦 产品明细 (<span id="vf-count">'+variants.length+'</span>条) <span style="font-weight:400;font-size:.75em;color:var(--text-dim)">点击行展开完整信息</span></h4>';
    h+='<div class="sr" style="margin:8px 0"><input id="vf" placeholder="搜索生产厂家 / 注册名称 / 商品名称 / 批准文号..." oninput="_filterVariants()"></div>';
    h+='<div id="vf-info" style="font-size:.72em;color:var(--text-dim);margin:0 0 4px"></div>';
    if(variants.length){
        h+='<div style="overflow-x:auto;max-height:600px;overflow-y:auto">';
        h+='<table style="font-size:.8em;min-width:900px" id="var-tbl"><thead><tr>';
        h+='<th style="width:6%">药品代码</th><th style="width:14%">注册名称</th><th style="width:10%">商品名称</th>';
        h+='<th style="width:7%">剂型</th><th style="width:10%">规格</th><th style="width:12%">包装</th>';
        h+='<th style="width:10%">企业</th><th style="width:10%">批准文号</th>';
        h+='</tr></thead><tbody>';
        variants.forEach(function(v,vi){
            var rn=v.reg_name||v.name||'';
            var tn=v.trade_name||'';
            var fm=v.dosage_form||v.form||'';
            var sp=v.spec||'';
            var pk=[v.pack_material,v.pack_qty,v.unit_prep,v.unit_pack].filter(Boolean).join(' ')||'—';
            var mf=v.manufacturer||'';
            var ap=v.approval||'';
            h+='<tr class="vrow" data-vi="'+vi+'">';
            h+='<td><span class="tag" style="font-family:monospace;font-size:.68em">'+(v.code||'—')+'</span></td>';
            h+='<td class="clamp" title="'+rn.replace(/"/g,'&quot;')+'">'+rn+'</td>';
            h+='<td class="clamp" title="'+tn.replace(/"/g,'&quot;')+'">'+(tn||'—')+'</td>';
            h+='<td>'+fm+'</td>';
            h+='<td>'+sp+'</td>';
            h+='<td style="font-size:.78em">'+pk+'</td>';
            h+='<td class="clamp" title="'+mf.replace(/"/g,'&quot;')+'">'+mf+'</td>';
            h+='<td style="font-size:.72em">'+(ap||'—')+'</td>';
            h+='</tr>';
            h+='<tr class="vdet" id="vd-'+vi+'" style="display:none"><td colspan="8">';
            h+='<div class="vdet-grid">';
            h+='<span class="vlbl">药品代码</span><span class="vval"><code>'+_trunc(v.code,80)+'</code></span>';
            h+='<span class="vlbl">注册名称</span><span class="vval">'+_trunc(rn,100)+'</span>';
            h+='<span class="vlbl">注册剂型</span><span class="vval">'+_trunc(v.reg_form,80)+'</span>';
            h+='<span class="vlbl">注册规格</span><span class="vval">'+_trunc(v.reg_spec,120)+'</span>';
            h+='<span class="vlbl">商品名称</span><span class="vval">'+_trunc(tn,100)+'</span>';
            h+='<span class="vlbl">剂型</span><span class="vval">'+_trunc(fm,80)+'</span>';
            h+='<span class="vlbl">规格</span><span class="vval">'+_trunc(sp,120)+'</span>';
            h+='<span class="vlbl">包装材质</span><span class="vval">'+_trunc(v.pack_material,120)+'</span>';
            h+='<span class="vlbl">最小包装数量</span><span class="vval">'+_trunc(v.pack_qty,30)+'</span>';
            h+='<span class="vlbl">最小制剂单位</span><span class="vval">'+_trunc(v.unit_prep,30)+'</span>';
            h+='<span class="vlbl">最小包装单位</span><span class="vval">'+_trunc(v.unit_pack,30)+'</span>';
            h+='<span class="vlbl">生产企业</span><span class="vval">'+_trunc(mf,120)+'</span>';
            h+='<span class="vlbl">批准文号</span><span class="vval">'+_trunc(ap,120)+'</span>';
            h+='<span class="vlbl">药品本位码</span><span class="vval"><code style="font-size:.85em">'+_trunc(v.barcode,80)+'</code></span>';
            h+='<span class="vlbl">📤 说明书</span><span class="vval">';
            h+='<label class="upload-btn" data-code="'+v.code.replace(/"/g,'&quot;')+'" title="上传该厂家药品说明书电子版">上传说明书 <input type="file" accept=".pdf,.jpg,.jpeg,.png" style="display:none" onchange="_uploadVariantRx(this.parentElement)"></label>';
            h+=' <span class="rx-up-files" id="rxu-'+vi+'" style="font-size:.78em;color:var(--text-dim)"></span>';
            h+='</span>';
            h+='</div></td></tr>';
        });
        h+='</tbody></table></div>';
    }else{
        // No product variants — allow creating via upload
        var drugCode='drug_'+d.id;
        h+='<div style="padding:12px 16px;background:var(--bg-input);border-radius:var(--r);border:1px dashed var(--border)">';
        h+='<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">';
        h+='<b style="font-size:.85em">📤 上传说明书创建产品明细:</b> ';
        h+='<label class="upload-btn" data-code="'+drugCode+'" data-drug-id="'+d.id+'" title="上传说明书电子版，自动生成产品明细记录">上传说明书 <input type="file" accept=".pdf,.jpg,.jpeg,.png" style="display:none" onchange="_uploadDrugRx(this.parentElement)"></label>';
        h+='<span class="rx-up-files" id="rxu-drug-'+d.id+'" style="font-size:.82em;color:var(--text-dim)"></span>';
        h+='</div>';
        h+='<div id="synth-vars-'+d.id+'" style="margin-top:8px"></div>';
        h+='</div>';
    }
    h+='</div>';

    // Rules
    var rules=d.rules||[];
    h+='<div class="detail-card">';
    h+='<h4>医保审核规则 ('+rules.length+'条)</h4>';
    if(rules.length){
        h+='<div style="overflow-x:auto;max-height:400px;overflow-y:auto">';
        h+='<table style="font-size:.82em"><thead><tr><th style="width:22%">药品名称</th><th style="width:34%">审核逻辑</th><th style="width:28%">依据</th><th style="width:16%">规则类别</th></tr></thead><tbody>';
        rules.forEach(function(r){
            h+='<tr>';
            h+='<td style="font-weight:500">'+(r.drug||r.code||'—')+'</td>';
            h+='<td>'+(r.rule||'—')+'</td>';
            h+='<td style="font-size:.78em;color:var(--text-dim)">'+_trunc(r.basis,80)+'</td>';
            h+='<td><span class="tag tag-w" style="font-size:.72em">'+_trunc(r.category,22)+'</span></td>';
            h+='</tr>';
        });
        h+='</tbody></table></div>';
    }else{
        h+='<p style="font-size:.82em;color:var(--text-dim)">暂无专项审核规则</p>';
    }
    h+='</div>';

    document.getElementById('drug-detail').innerHTML=h;
    // Load uploaded files for each variant
    if(variants.length){
        variants.forEach(function(v,vi){
            _loadVariantUploads(v.code, 'rxu-'+vi);
        });
    }else{
        // Zero variants — check for drug-level uploads and render synthetic entries
        _loadDrugUploads('drug_'+d.id, d);
    }
    setTimeout(function(){
        document.querySelectorAll('.vrow').forEach(function(r){
            r.onclick=function(){
                var vi=this.getAttribute('data-vi');
                var det=document.getElementById('vd-'+vi);
                if(det)det.style.display=det.style.display==='none'?'table-row':'none';
            };
        });
    },50);
}

// === PHARMACOPOEIA SEARCH ===
function _pharmSearch(){
    if(!_pharm){document.getElementById('pharm-tb').innerHTML='<tr><td colspan="6" class="emp">药典索引加载中...</td></tr>';return}
    var q=(document.getElementById('qp').value||'').toLowerCase();
    var r=_pharm;
    if(q){
        r=_pharm.filter(function(p){
            if((p.name||'').toLowerCase().indexOf(q)>=0)return true;
            if((p.pinyin||'').toLowerCase().indexOf(q)>=0)return true;
            if((p.latin||'').toLowerCase().indexOf(q)>=0)return true;
            return false;
        });
    }
    document.getElementById('pharm-info').textContent=q?'搜索匹配 '+r.length+' 条药典词条（共 '+_pharm.length+' 条）':'共 '+_pharm.length.toLocaleString()+' 条药典词条（2025版）';
    var show=r.slice(0,200);
    document.getElementById('pharm-tb').innerHTML=show.map(function(p){
        var h='<tr>';
        h+='<td style="font-weight:500">'+p.name+'</td>';
        h+='<td style="font-family:monospace;font-size:.8em;color:var(--accent)">'+p.pinyin+'</td>';
        h+='<td style="font-size:.78em;color:var(--text-dim)">'+(p.latin||'—')+'</td>';
        h+='<td><span class="tag tag-a">'+p.volume+'</span></td>';
        h+='<td style="font-weight:600;font-size:1.1em;color:var(--accent)">'+p.page+'</td>';
        h+='<td style="font-size:.75em">';
        h+='<a href="/pdf?id='+p.fid+'#page='+p.page+'" target="_blank" style="color:var(--accent);text-decoration:none;margin-right:8px">[打开]</a>';
        h+='<span style="cursor:pointer;color:var(--success)" onclick="_previewPage(\''+p.fid+'\','+p.page+',this)">[预览]</span>';
        h+='</td></tr>';
        return h;
    }).join('');
}

// === RULES BROWSING ===
var _rulesData=null;
function _loadRules(){
    if(_rulesData){_renderRules();return}
    document.getElementById('rules-content').innerHTML='<div class="emp"><div class="spinner"></div><p>加载审核规则...</p></div>';
    fetch('audit_rules.json').then(function(r){return r.json()}).then(function(d){
        _rulesData=d;_renderRules();
    }).catch(function(e){
        document.getElementById('rules-content').innerHTML='<div class="emp"><p>规则加载失败: '+e.message+'</p></div>';
    });
}

function _renderRules(){
    var d=_rulesData;
    if(!d||!d.length){document.getElementById('rules-content').innerHTML='<div class="emp"><p>无规则数据</p></div>';return}

    // Group by rule_type
    var groups={};
    d.forEach(function(r){
        var t=r.rule_type||'其他';
        if(!groups[t])groups[t]=[];
        groups[t].push(r);
    });

    var h='<div class="sr" style="margin-top:8px"><input id="qr" placeholder="搜索规则 / 药品名称..." oninput="_renderRules()"></div>';
    h+='<div id="rules-info" style="font-size:.78em;color:var(--text-dim);margin:8px 0">共 '+d.length+' 条审核规则，'+Object.keys(groups).length+' 个类别</div>';

    var q=(document.getElementById('qr')||{}).value||'';
    q=q.toLowerCase();

    Object.keys(groups).sort().forEach(function(cat){
        var rules=groups[cat];
        if(q){
            rules=rules.filter(function(r){
                if((r.rule_type||'').toLowerCase().indexOf(q)>=0)return true;
                if((r.drug_name||'').toLowerCase().indexOf(q)>=0)return true;
                if((r.check_logic||'').toLowerCase().indexOf(q)>=0)return true;
                if((r.logic_basis||'').toLowerCase().indexOf(q)>=0)return true;
                return false;
            });
        }
        if(!rules.length)return;

        h+='<div class="rule-group" style="margin:16px 0">';
        h+='<h4 style="cursor:pointer;padding:8px 12px;background:var(--bg-input);border-radius:var(--r);font-size:.9em" onclick="var n=this.nextElementSibling;n.style.display=n.style.display===\'none\'?\'\':\'none\'"> '+cat+' <span style="font-weight:400;font-size:.8em;color:var(--text-dim)">('+rules.length+'条)</span></h4>';
        h+='<div class="rule-list">';
        h+='<table style="font-size:.85em"><thead><tr><th style="width:20%">药品名称</th><th style="width:36%">审核逻辑</th><th style="width:28%">依据</th><th style="width:16%">规则类别</th></tr></thead><tbody>';
        rules.forEach(function(r){
            h+='<tr>';
            h+='<td style="font-weight:500">'+(r.drug_name||'—')+'</td>';
            h+='<td style="font-size:.82em">'+(r.check_logic||'—')+'</td>';
            h+='<td style="font-size:.78em;color:var(--text-dim)">'+_trunc(r.logic_basis,80)+'</td>';
            h+='<td><span class="tag tag-w" style="font-size:.72em">'+_trunc(r.rule_type,22)+'</span></td>';
            h+='</tr>';
        });
        h+='</tbody></table></div></div>';
    });

    document.getElementById('rules-content').innerHTML=h;
}

// === VARIANT SEARCH ===
function _filterVariants(){
    var q=(document.getElementById('vf')||{}).value||''; q=q.toLowerCase();
    var total=0, shown=0;
    document.querySelectorAll('#var-tbl .vrow').forEach(function(r){
        total++;
        var txt=r.textContent.toLowerCase();
        var match=!q||txt.indexOf(q)>=0;
        r.style.display=match?'':'none';
        var vi=r.getAttribute('data-vi');
        var det=document.getElementById('vd-'+vi);
        if(det&&!match)det.style.display='none';
        if(match)shown++;
    });
    var cnt=document.getElementById('vf-count');
    if(cnt)cnt.textContent=shown;
    var info=document.getElementById('vf-info');
    if(info)info.textContent=q?'显示 '+shown+'/'+total+' 条':'';
}

// === DRUG-LEVEL UPLOAD (for drugs with 0 variants) ===
function _uploadDrugRx(el){
    var code=el.getAttribute('data-code')||'';
    var drugId=el.getAttribute('data-drug-id')||'';
    var fileInput=el.querySelector('input[type=file]');
    var file=fileInput.files[0];
    if(!file)return;
    var formData=new FormData();
    formData.append('file', file);
    var span=el.parentElement.querySelector('.rx-up-files');
    if(span)span.textContent='上传中...';
    fetch('/upload?drug='+encodeURIComponent(code), {method:'POST', body:formData})
    .then(function(r){return r.json()})
    .then(function(d){
        if(d.ok){
            var msg='✅ '+d.filename;
            if(d.extracted){
                var ex=d.extracted;
                var parts=[];
                if(ex.reg_name) parts.push(ex.reg_name);
                if(ex.manufacturer) parts.push(ex.manufacturer);
                if(ex.approval) parts.push(ex.approval);
                if(parts.length) msg+=' ('+parts.join(' | ')+')';
            }
            if(span)span.textContent=msg;
            // Re-render synthetic variants with extracted fields
            var synthDiv=document.getElementById('synth-vars-'+drugId);
            if(synthDiv){
                _loadDrugUploads(code, null, drugId);
            }
        }else{
            if(span)span.textContent='❌ 失败';
        }
    }).catch(function(e){
        if(span)span.textContent='❌ '+e.message;
    });
    fileInput.value='';
}

function _loadDrugUploads(code, drug, drugId){
    // drugId is for the synth-vars div; drug is the drug object (optional)
    var did=drugId||(drug?drug.id:'');
    var synthDiv=document.getElementById('synth-vars-'+did);
    if(!synthDiv)return;
    fetch('/uploads_list?drug='+encodeURIComponent(code||''))
    .then(function(r){return r.json()})
    .then(function(d){
        if(!d.files||!d.files.length){synthDiv.innerHTML='';return}
        var h='<table style="font-size:.8em;min-width:860px;margin-top:6px"><thead><tr>';
        h+='<th style="width:13%">说明书文件</th>';
        h+='<th style="width:12%">注册名称</th><th style="width:7%">商品名</th>';
        h+='<th style="width:6%">剂型</th><th style="width:8%">规格</th>';
        h+='<th style="width:14%">生产企业</th><th style="width:11%">批准文号</th>';
        h+='<th style="width:9%">包装</th><th style="width:8%">上传时间</th><th style="width:12%">操作</th>';
        h+='</tr></thead><tbody>';
        d.files.forEach(function(f,vi){
            var parts=f.name.split('_');
            var ts=parts[0];
            var orgName=parts.slice(1).join('_')||f.name;
            var tsStr='';
            if(/^\d{10}$/.test(ts)){
                var dt=new Date(parseInt(ts)*1000);
                tsStr=dt.getFullYear()+'-'+(dt.getMonth()+1)+'-'+dt.getDate();
            }
            var size=f.size>1048576?(f.size/1048576).toFixed(1)+'MB':(f.size/1024).toFixed(0)+'KB';
            var ex=f.extracted||{};
            var regName=ex.reg_name||'';
            var tradeName=ex.trade_name||'';
            var dosageForm=ex.dosage_form||'';
            var spec=ex.spec||'';
            var manufacturer=ex.manufacturer||'';
            var approval=ex.approval||'';
            var packaging=ex.packaging||'';
            var hasExtracted=!!(ex.reg_name||ex.approval||ex.manufacturer);
            var rowStyle=hasExtracted?'background:#f0fdf4;border-left:3px solid var(--success)':'';
            h+='<tr style="'+rowStyle+'">';
            h+='<td style="font-size:.76em"><a href="'+f.url+'" target="_blank" style="color:var(--accent);text-decoration:none" title="大小:'+size+'">📎 '+_trunc(orgName,22)+'</a></td>';
            h+='<td style="font-size:.78em;font-weight:500">'+(regName||'<span style="color:var(--text-dim)">（待提取）</span>')+'</td>';
            h+='<td style="font-size:.74em">'+(tradeName||'<span style="color:var(--text-dim)">—</span>')+'</td>';
            h+='<td style="font-size:.74em">'+(dosageForm||'<span style="color:var(--text-dim)">—</span>')+'</td>';
            h+='<td style="font-size:.74em">'+(spec||'<span style="color:var(--text-dim)">—</span>')+'</td>';
            h+='<td style="font-size:.74em">'+(manufacturer||'<span style="color:var(--text-dim)">（待提取）</span>')+'</td>';
            h+='<td style="font-size:.7em"><code>'+(approval||'<span style="color:var(--text-dim)">—</span>')+'</code></td>';
            h+='<td style="font-size:.68em;color:var(--text-dim);max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+_trunc(packaging,200)+'">'+(packaging||'—')+'</td>';
            h+='<td style="font-size:.7em;color:var(--text-dim)">'+tsStr+'</td>';
            h+='<td style="font-size:.68em">';
            h+='<label class="upload-btn" data-code="'+code.replace(/"/g,'&quot;')+'" data-drug-id="'+did+'" style="font-size:.66em" title="追加上传更多说明书">追加上传 <input type="file" accept=".pdf,.jpg,.jpeg,.png" style="display:none" onchange="_uploadDrugRx(this.parentElement)"></label>';
            h+='</td>';
            h+='</tr>';
        });
        h+='</tbody></table>';
        synthDiv.innerHTML=h;
        var span=document.getElementById('rxu-drug-'+did);
        if(span)span.textContent=d.files.length+' 份说明书已上传';
    }).catch(function(){synthDiv.innerHTML='';});
}

// === VARIANT-LEVEL FILE UPLOAD ===
function _uploadVariantRx(el){
    var code=el.getAttribute('data-code')||'';
    var fileInput=el.querySelector('input[type=file]');
    var file=fileInput.files[0];
    if(!file)return;
    var formData=new FormData();
    formData.append('file', file);
    // Find the nearest status span
    var span=el.parentElement.querySelector('.rx-up-files');
    if(span)span.textContent='上传中...';
    fetch('/upload?drug='+encodeURIComponent(code), {method:'POST', body:formData})
    .then(function(r){return r.json()})
    .then(function(d){
        if(d.ok){
            if(span)span.textContent='✅ '+d.filename;
            _loadVariantUploads(code, span.id);
        }else{
            if(span)span.textContent='❌ 失败';
        }
    }).catch(function(e){
        if(span)span.textContent='❌ '+e.message;
    });
    fileInput.value='';
}

function _loadVariantUploads(code, spanId){
    var span=document.getElementById(spanId);
    if(!span)return;
    fetch('/uploads_list?drug='+encodeURIComponent(code||''))
    .then(function(r){return r.json()})
    .then(function(d){
        if(!d.files||!d.files.length){span.innerHTML='';return}
        span.innerHTML=d.files.map(function(f){
            return ' 📎<a href="'+f.url+'" target="_blank" style="color:var(--accent);text-decoration:none;font-size:.85em">'+f.name+'</a>';
        }).join('');
        // Highlight the parent row to indicate uploaded files
        var row=span.closest('tr.vdet');
        if(row){
            var prevRow=row.previousElementSibling;
            if(prevRow&&prevRow.classList.contains('vrow')){
                prevRow.style.background='#f0fdf4';
                prevRow.style.borderLeft='3px solid var(--success)';
            }
            // Also mark the expanded detail section
            var lbl=row.querySelector('.vlbl');
            if(lbl&&lbl.textContent.indexOf('📤')>=0){
                lbl.style.color='var(--success)';
                lbl.style.fontWeight='700';
            }
        }
    }).catch(function(){span.innerHTML=''});
}

function _trunc(s,n){n=n||120;return s&&s.length>n?s.slice(0,n)+'…':s;}

// Page text preview (uses server-side cache, instant response)
function _previewPage(fid, page, el){
    var next=el.parentElement.querySelector('.preview-box');
    if(next){next.remove();return;}
    var box=document.createElement('div');
    box.className='preview-box';
    box.style.cssText='margin-top:6px;padding:10px;background:#fff;border:1px solid var(--border);border-radius:var(--r-sm);font-size:.78em;max-height:300px;overflow-y:auto;white-space:pre-wrap;line-height:1.5';
    box.textContent='加载中...';
    el.parentElement.appendChild(box);
    fetch('/page_text?id='+fid+'&page='+page).then(function(r){return r.json()}).then(function(d){
        box.textContent=d.text||'(无文字内容)';
    }).catch(function(e){
        box.textContent='加载失败: '+e.message;
    });
}
// Column resize
setTimeout(function(){
    document.querySelectorAll('table').forEach(function(tbl){
        _makeResizable(tbl);
    });
},1000);

function _makeResizable(tbl){
    tbl.querySelectorAll('th').forEach(function(th,i){
        if(th.querySelector('.rh'))return;
        var rh=document.createElement('div');rh.className='rh';th.appendChild(rh);
        var sx,sw;
        rh.addEventListener('mousedown',function(e){
            sx=e.clientX;sw=th.offsetWidth;
            rh.classList.add('active');
            document.body.style.cursor='col-resize';
            function mv(ev){var w=sw+(ev.clientX-sx);if(w>60)th.style.width=w+'px'}
            function up(){
                rh.classList.remove('active');
                document.body.style.cursor='';
                document.removeEventListener('mousemove',mv);
                document.removeEventListener('mouseup',up);
            }
            document.addEventListener('mousemove',mv);
            document.addEventListener('mouseup',up);
        });
    });
}
