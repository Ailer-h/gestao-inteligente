import type { RecordData } from './resources'

export interface Enrollment { id: number; status: number; data_entrada: string }
export interface EnrollmentState { options: RecordData[]; selected: Enrollment[]; original: Enrollment[]; error?: string }

export function enrollmentPayload(state: EnrollmentState): Enrollment[] | null {
  const normalize = (items: Enrollment[]) => JSON.stringify([...items].sort((a, b) => a.id - b.id))
  return normalize(state.selected) === normalize(state.original) ? null : state.selected
}
