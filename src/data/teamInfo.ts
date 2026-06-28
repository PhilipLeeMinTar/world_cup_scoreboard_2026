/** Flag emoji + Chinese name for every team that can appear in the knockout stage. */
export interface TeamInfo {
  flag: string;
  zh: string;
}

const TEAM_INFO: Record<string, TeamInfo> = {
  // Group A
  'Mexico':                  { flag: '🇲🇽', zh: '墨西哥' },
  'South Africa':            { flag: '🇿🇦', zh: '南非' },
  // Group B
  'Canada':                  { flag: '🇨🇦', zh: '加拿大' },
  'USA':                     { flag: '🇺🇸', zh: '美国' },
  'Bosnia & Herzegovina':    { flag: '🇧🇦', zh: '波黑' },
  'Switzerland':             { flag: '🇨🇭', zh: '瑞士' },
  // Group C
  'Brazil':                  { flag: '🇧🇷', zh: '巴西' },
  'Morocco':                 { flag: '🇲🇦', zh: '摩洛哥' },
  // Group D
  'Paraguay':                { flag: '🇵🇾', zh: '巴拉圭' },
  'Australia':               { flag: '🇦🇺', zh: '澳大利亚' },
  // Group E
  'Germany':                 { flag: '🇩🇪', zh: '德国' },
  'Ivory Coast':             { flag: '🇨🇮', zh: '科特迪瓦' },
  'Ecuador':                 { flag: '🇪🇨', zh: '厄瓜多尔' },
  // Group F
  'Netherlands':             { flag: '🇳🇱', zh: '荷兰' },
  'Japan':                   { flag: '🇯🇵', zh: '日本' },
  'Sweden':                  { flag: '🇸🇪', zh: '瑞典' },
  // Group G
  'Belgium':                 { flag: '🇧🇪', zh: '比利时' },
  'Egypt':                   { flag: '🇪🇬', zh: '埃及' },
  // Group H
  'Spain':                   { flag: '🇪🇸', zh: '西班牙' },
  'Cabo Verde':              { flag: '🇨🇻', zh: '佛得角' },
  // Group I
  'France':                  { flag: '🇫🇷', zh: '法国' },
  'Senegal':                 { flag: '🇸🇳', zh: '塞内加尔' },
  'Norway':                  { flag: '🇳🇴', zh: '挪威' },
  // Group J
  'Argentina':               { flag: '🇦🇷', zh: '阿根廷' },
  'Algeria':                 { flag: '🇩🇿', zh: '阿尔及利亚' },
  'Austria':                 { flag: '🇦🇹', zh: '奥地利' },
  // Group K
  'Portugal':                { flag: '🇵🇹', zh: '葡萄牙' },
  'Congo DR':                { flag: '🇨🇩', zh: '刚果民主共和国' },
  'Colombia':                { flag: '🇨🇴', zh: '哥伦比亚' },
  // Group L
  'England':                 { flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', zh: '英格兰' },
  'Croatia':                 { flag: '🇭🇷', zh: '克罗地亚' },
  'Ghana':                   { flag: '🇬🇭', zh: '加纳' },
  // API name aliases
  'DR Congo':                { flag: '🇨🇩', zh: '刚果民主共和国' },
  'Cape Verde':              { flag: '🇨🇻', zh: '佛得角' },
  'South Korea':             { flag: '🇰🇷', zh: '韩国' },
  'Serbia':                  { flag: '🇷🇸', zh: '塞尔维亚' },
  'Tunisia':                 { flag: '🇹🇳', zh: '突尼斯' },
};

export function getTeamInfo(name: string): TeamInfo {
  return TEAM_INFO[name] ?? { flag: '🏳️', zh: name };
}
