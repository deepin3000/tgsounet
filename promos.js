/**
 * TGSOU 全站推广位配置（唯一数据源）
 *
 * 修改本文件后 git push 即全站生效（约 20 秒自动部署）。
 * 每个条目字段：
 *   title    推广标题（必填）
 *   desc     描述文字，悬停显示（必填）
 *   link     跳转链接（必填；站外链接自动经 /link/ 跳转页）
 *   image    背景图 URL（与 gradient 二选一，image 优先）
 *   gradient CSS 渐变背景，无图时使用
 *   icon     Font Awesome 图标类名，如 "fa-brands fa-telegram"
 *   tag      左上角角标文字，默认 "推荐"
 *   display  "always" 常显 | "hover" 悬停显示，默认 hover
 *   priority 排序权重（可选，数字越小越靠前）：
 *            - 设置了 priority 的条目为「常驻位」，排在最前且不参与轮换/随机；
 *            - 未设置 priority 的条目排在中间（首页轮换、详情页随机）；
 *            - priority >= 9000 视为「补位」（如广告位招租），永远排在最后，
 *              且仅在还有空位时才显示。
 *
 * 建议结构：常驻 1~3 条（priority 1、2、3...）+ 若干中间条目 + 招租补位（9999）。
 * 首页推广区展示最多 10 位；详情页随机取 2~3 条。
 */
window.adPoolData = [
  {
    title: 'TGwiki',
    desc: '由寻花楼打造的精选老师',
    link: 'https://t.me/brobusbot',
    image: '/promos/xunhualou.jpg',
    icon: 'fa-brands fa-telegram',
    gradient: 'linear-gradient(135deg, #00C6FF 0%, #0072FF 100%)',
    tag: '知识库',
    display: 'always',
    priority: 1,
  },
  {
    title: '搜搜',
    desc: 'Telegram 中文搜索与群主增长平台。搜索群组、频道和内容，管理群聊与频道，并通过 AI 提升安全、运营与增长效率。',
    link: 'https://t.me/soso?start=usecode_1309752572',
    image: '/promos/soso.jpg',
    icon: 'fa-brands fa-telegram',
    gradient: 'linear-gradient(135deg, #00C6FF 0%, #0072FF 100%)',
    tag: '搜索',
    display: 'always',
  },
  {
    title: '极搜',
    desc: 'Telegram必备的搜索引擎',
    link: 'https://t.me/jisou2?start=a_1309752572',
    image: '/promos/jisu.jpg',
    icon: 'fa-brands fa-telegram',
    gradient: 'linear-gradient(135deg, #00C6FF 0%, #0072FF 100%)',
    tag: '搜索',
    display: 'always',
  },
  {
    title: '神马搜索',
    desc: '全功能中文搜索机器人',
    link: 'https://t.me/smss?start=spread_1309752572',
    image: '/promos/smss.jpg',
    icon: 'fa-brands fa-telegram',
    gradient: 'linear-gradient(135deg, #00C6FF 0%, #0072FF 100%)',
    tag: '搜索',
    display: 'always',
  },
  {
    title: '广告位招租',
    desc: '在 TGSOU 全站推广您的频道/群组/产品，联系 @tgsounetbot',
    link: 'https://t.me/tgsounetbot',
    icon: 'fa-solid fa-rectangle-ad',
    gradient: 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)',
    tag: '招租',
    display: 'always',
    priority: 9999,
  },
];
