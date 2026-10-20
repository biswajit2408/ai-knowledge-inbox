// "1 chunk", "3 chunks"
export function pluralize(count, word) {
  return `${count} ${word}${count === 1 ? '' : 's'}`
}
