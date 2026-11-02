import type { TenderQuestion } from './quickSale'

/** Keep the visible question complete; only the tender-choice audio is brief. */
export function spokenPaymentQuestion(question: Pick<TenderQuestion, 'question' | 'missing'>): string {
  return question.missing.includes('tender') ? 'Cash or bank?' : question.question
}
export const SALE_SAVED_SPEECH = 'Sale saved'
