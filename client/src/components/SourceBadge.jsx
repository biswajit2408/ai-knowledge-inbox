import { Link2, StickyNote } from 'lucide-react'

import { Badge } from '@/components/ui/badge'

export function SourceBadge({ type }) {
  return type === 'url' ? (
    <Badge variant="outline">
      <Link2 />
      URL
    </Badge>
  ) : (
    <Badge variant="secondary">
      <StickyNote />
      Note
    </Badge>
  )
}
