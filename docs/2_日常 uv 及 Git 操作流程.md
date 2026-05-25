
## uv 操作流程
激活项目：

```bash
cd 本项目
```

```bash
.venv\Scripts\activate
```

安装新依赖：
```bash
uv add xxx
```


## 编程流程
1. 明确需求
2. 编写代码，测试验证
3. 编写文档，记录开发过程和总结
4. 提交 Git，开 PR，Merge


## Git 使用流程
版本控制：
```bash
git checkout main
git pull origin main
git checkout -b feature/xxx

# 开发中反复
git add .
git commit -m "feat: xxx"

git push -u origin feature/xxx
# 去 GitHub 开 PR 并 Merge

git checkout main
git pull origin main
git branch -d feature/xxx
git push origin --delete feature/xxx
git fetch -p
```
