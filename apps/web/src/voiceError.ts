export function voiceErrorSummary(message: string, uncertain = false) {
  if (uncertain) return 'No sale receipt received. Restore the shop connection. Recover the original request.'
  if (/Could not reach or read the voice service/.test(message)) return 'Voice service is unavailable. Retry or check Shop Connection in Profile.'
  if (/product not found/i.test(message)) return 'Product not found. No sale recorded. Say Apo to try again.'
  return message
}
