# 主数据导入样例

将 CSV 复制后修改，或通过 Excel 维护多 Sheet（customers / machines / boms / bom_items / users）。

```bash
cd backend
python scripts/import_initial_master_data.py --dir data/import_samples --dry-run
python scripts/import_initial_master_data.py --dir data/import_samples
```

导入前请先执行 `bootstrap_admin.py`；用户导入需先执行 `setup_trial_users.py`。
