import subprocess
except Exception as e:
    print(f'ETL失败: {e}')
    exit(1)
except:
    print('ETL完成')
    exit(0)

echo '>>> 开始清洗ICD-10等级结构'
subprocess.run(['python', 'build_icd10_hierarchy.py'])

# 添加其他需要执行的步骤
