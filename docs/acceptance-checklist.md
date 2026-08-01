# 包包刺绣 DIY 商城验收清单

## 本地启动

```powershell
cd D:\diy-bag-platform
docker compose up -d --build
docker compose exec api python -m alembic upgrade head
```

- API 健康检查：`http://localhost:8000/api/health` 返回 `{"status":"ok"}`。
- 商家后台：`http://localhost:5173`。
- 用户端 H5：`http://localhost:5174/#/pages/editor/index`。

## 商家后台

- 上传包包图片、填写毫米尺寸与基础价格。
- 在图片上配置刺绣区域，确认保存的是相对坐标与实际毫米尺寸。
- 创建图案分类和图案，上传图片、填写固定宽高、价格和生产编号。
- 编辑图案的图片、尺寸或价格后，确认会产生新的图案版本。
- 上架包包与图案；已归档数据不再出现在用户端目录中。
- 在系统设置中调整单设备最多可保存的设计数。

## 用户端 DIY

- 顶部横滑选择已上架包包。
- 点击左侧分类，确认图案面板弹出。
- 连续点击同一图案，确认可不限数量添加。
- 单指拖动图案，确认图案不能超出虚线刺绣区域。
- 选中图案后拖动蓝色旋转手柄，确认可以旋转但没有缩放入口。
- 刷新页面后，画布草稿和已保存设计仍可恢复；删除已保存设计后列表实时更新。
- 以不同窗口宽度打开页面，确认图案相对位置与毫米尺寸比例保持一致。

## 模拟订单与生产

- 保存设计，在确认页创建模拟订单。
- 在“我的模拟订单”中完成模拟付款。
- 后台订单列表确认金额、包包和图案固定尺寸来自订单快照。
- 订单按“已付款 → 待制作 → 制作中 → 已发货 → 已完成”更新；发货必须填写物流单号。
- 已付款订单可在后台打开生产效果图；普通 `/api/files/...` 地址不能访问生产图。

## 自动化检查

```powershell
cd D:\diy-bag-platform\services\api
.\.venv\Scripts\python.exe -m pytest -q tests

cd D:\diy-bag-platform\apps\miniapp
npm run type-check
npm run test
npm run build:h5

cd D:\diy-bag-platform\apps\admin-web
npm run type-check
npm run build
```

## 当前限制

- “模拟付款”不调用任何真实支付渠道。
- 当前以设备 `client_key` 区分设计和订单；抖音授权登录接入后应替换为平台用户身份。
- 抖音小程序产物构建仍受当前 uni-app alpha 包内部 Vue 版本冲突影响；H5 开发构建正常。升级到一组官方匹配的稳定版 DCloud/uni-app 依赖后应重新执行 `npm run build:mp-toutiao`。
- 管理后台目前是开发期界面，尚未接入正式管理员鉴权与权限控制；生产图接口在接入鉴权前仅适用于受控开发环境。
