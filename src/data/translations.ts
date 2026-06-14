/**
 * Chinese translations for team/country names used in the scoreboard.
 * Keyed by the English name as used in groups.ts and the API.
 */
export const TEAM_ZH: Record<string, string> = {
  // Group A
  'Mexico': '墨西哥',
  'South Africa': '南非',
  'South Korea': '韩国',
  'Czechia': '捷克',

  // Group B
  'Canada': '加拿大',
  'Bosnia and Herzegovina': '波黑',
  'Qatar': '卡塔尔',
  'Switzerland': '瑞士',

  // Group C
  'Brazil': '巴西',
  'Morocco': '摩洛哥',
  'Haiti': '海地',
  'Scotland': '苏格兰',

  // Group D
  'United States': '美国',
  'Paraguay': '巴拉圭',
  'Australia': '澳大利亚',
  'Türkiye': '土耳其',

  // Group E
  'Germany': '德国',
  "Curaçao": '库拉索',
  'Ivory Coast': '科特迪瓦',
  'Ecuador': '厄瓜多尔',

  // Group F
  'Netherlands': '荷兰',
  'Japan': '日本',
  'Sweden': '瑞典',
  'Tunisia': '突尼斯',

  // Group G
  'Belgium': '比利时',
  'Egypt': '埃及',
  'IR Iran': '伊朗',
  'New Zealand': '新西兰',

  // Group H
  'Spain': '西班牙',
  'Cabo Verde': '佛得角',
  'Saudi Arabia': '沙特阿拉伯',
  'Uruguay': '乌拉圭',

  // Group I
  'France': '法国',
  'Senegal': '塞内加尔',
  'Iraq': '伊拉克',
  'Norway': '挪威',

  // Group J
  'Argentina': '阿根廷',
  'Algeria': '阿尔及利亚',
  'Austria': '奥地利',
  'Jordan': '约旦',

  // Group K
  'Portugal': '葡萄牙',
  'Congo DR': '刚果(金)',
  'Uzbekistan': '乌兹别克斯坦',
  'Colombia': '哥伦比亚',

  // Group L
  'England': '英格兰',
  'Croatia': '克罗地亚',
  'Ghana': '加纳',
  'Panama': '巴拿马',

  // Other names that may appear from the API
  'Iran': '伊朗',
};

/**
 * Get the Chinese name for a team, returning the English name if not found.
 */
export function teamZh(name: string): string {
  return TEAM_ZH[name] || name;
}
