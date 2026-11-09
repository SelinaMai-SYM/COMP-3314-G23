# 环境

库代码不读取数据文件，也没有写死绝对路径。测试从 `v1` 目录运行：

```bash
python3 -m pytest
```

`pyproject.toml` 把仓库根目录放进 `pythonpath`，因此不需要先 `pip install -e`。

## 本机已核对的解释器

系统 Python：`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`，版本 3.13.3。

当时已经安装、并被测试使用的版本：

| 包 | 版本 |
| --- | --- |
| numpy | 2.4.2 |
| scipy | 1.17.1 |
| scikit-learn | 1.8.0 |
| pandas | 2.3.3 |
| matplotlib | 3.10.8 |
| PyYAML | 6.0.3 |
| pytest | 9.1.1 |

pytest 9.1.1 和可选的 cvxpy 1.9.3（CLARABEL）是用 `python3 -m pip install --user` 装到用户目录的，不在本仓库里。默认证书校验连不上 PyPI，安装时加了 `--trusted-host pypi.org --trusted-host files.pythonhosted.org`。cvxpy 只供 `tests/test_ssc.py` 里的凸问题对照；没有 cvxpy 时该测试会被 `pytest.importorskip` 跳过。式 (12) 的二次目标对照使用 `scipy.optimize` 的 L-BFGS-B，不依赖 cvxpy。

Anaconda 的 scikit-learn 与当前 numpy 二进制不兼容，测试没有用 `/opt/anaconda3/bin/python`。

## 磁盘

数据盘当时约剩 9.2 GiB。不要在仓库里创建虚拟环境或放入原始图像。依赖列表在 `requirements.txt`。
