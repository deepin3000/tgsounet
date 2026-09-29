/**
 * TGSOU 全站推广位配置（唯一数据源）
 *
 * 修改本文件后 git push 即全站生效（约 20 秒自动部署）。
 * 每个条目字段：
 *   title   推广标题（必填）
 *   desc    描述文字，悬停显示（必填）
 *   link    跳转链接（必填；站外链接自动经 /link/ 跳转页）
 *   image   背景图 URL（与 gradient 二选一，image 优先）
 *   gradient CSS 渐变背景，无图时使用
 *   icon    Font Awesome 图标类名，如 "fa-brands fa-telegram"
 *   tag     左上角角标文字，默认 "推荐"
 *   display "always" 常显 | "hover" 悬停显示，默认 hover
 *
 * 建议 3~9 条；首页推广区轮换展示 10 位（不足则循环），详情页随机取 2~3 条。
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
  },
  {
    title: '广告位招租',
    desc: '在 TGSOU 全站推广您的频道/群组/产品，联系 @tgsou0bot',
    link: 'https://t.me/tgsou0bot',
    icon: 'fa-solid fa-rectangle-ad',
    gradient: 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)',
    tag: '招租',
    display: 'always',
  },
];
