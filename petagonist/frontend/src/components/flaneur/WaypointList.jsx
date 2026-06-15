import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import Button from '../ui/Button'
import Tag from '../ui/Tag'
import { getType } from '../../utils/waypointTypes'

/**
 * WaypointList — ordered list of dropped waypoints. Drag to reorder, delete
 * per row. "Generate Comic" unlocks at 2+ waypoints.
 */
export default function WaypointList({ waypoints, max, onRemove, onMove, onSelectPhoto, onGenerate }) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  function handleDragEnd(e) {
    const { active, over } = e
    if (!over || active.id === over.id) return
    const from = waypoints.findIndex((w) => w.id === active.id)
    const to = waypoints.findIndex((w) => w.id === over.id)
    if (from !== -1 && to !== -1) onMove(from, to)
  }

  const enough = waypoints.length >= 2

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-lg font-black text-white">Your route</h3>
        <Tag tone={enough ? 'lime' : 'cream'}>
          {waypoints.length}/{max}
        </Tag>
      </div>

      {waypoints.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center rounded-[var(--radius-soft)] border-2 border-dashed border-white/25 p-6 text-center">
          <span className="text-4xl">📍</span>
          <p className="mt-2 font-display font-bold text-white">No stops yet</p>
          <p className="mt-1 text-sm text-white/60">
            Click the map to drop your first waypoint.
          </p>
        </div>
      ) : (
        <div className="flex-1 space-y-2 overflow-y-auto pr-1">
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={waypoints.map((w) => w.id)} strategy={verticalListSortingStrategy}>
              {waypoints.map((w, i) => (
                <SortableRow key={w.id} w={w} index={i} onRemove={onRemove} onSelectPhoto={onSelectPhoto} />
              ))}
            </SortableContext>
          </DndContext>
        </div>
      )}

      <div className="mt-4">
        <Button variant="lime" size="lg" className="w-full" disabled={!enough} onClick={onGenerate}>
          Generate Comic →
        </Button>
        {!enough && (
          <p className="mt-2 text-center text-sm text-white/60">
            Drop at least 2 waypoints to make a strip.
          </p>
        )}
      </div>
    </div>
  )
}

function SortableRow({ w, index, onRemove, onSelectPhoto }) {
  const type = getType(w.type)
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: w.id })
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : undefined,
  }

  const photos = w.photos
  const selectedId = w.selectedPhoto?.id

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`rounded-[var(--radius-soft)] bg-white/10 p-3 ${
        isDragging ? 'shadow-[var(--shadow-lift)] ring-2 ring-sun' : ''
      }`}
    >
      <div className="flex items-center gap-3">
        <button
          {...attributes}
          {...listeners}
          className="cursor-grab touch-none px-1 text-white/50 hover:text-white active:cursor-grabbing"
          aria-label="Drag to reorder"
        >
          ⠿
        </button>

        <Tag tone="grape" className="h-8 w-8 justify-center !rounded-full">
          {index + 1}
        </Tag>

        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1.5 truncate font-display text-sm font-extrabold text-white">
            <span title={type.label}>{type.icon}</span>
            <span className="truncate">{w.name || `${type.label} stop`}</span>
          </p>
          <p className="truncate text-xs text-white/60">
            {w.lat.toFixed(4)}, {w.lng.toFixed(4)}
          </p>
        </div>

        <button
          onClick={() => onRemove(w.id)}
          className="spring grid h-7 w-7 place-items-center rounded-full bg-white/10 text-white/70 hover:bg-tang hover:text-white"
          aria-label={`Remove stop ${index + 1}`}
        >
          ✕
        </button>
      </div>

      {/* Scene photo picker */}
      {photos === null && (
        <div className="mt-2 flex gap-1.5 overflow-x-auto">
          <div className="h-12 w-16 animate-pulse rounded bg-white/10" />
          <div className="h-12 w-16 animate-pulse rounded bg-white/10" />
          <div className="h-12 w-16 animate-pulse rounded bg-white/10" />
        </div>
      )}
      {photos && photos.length > 0 && (
        <div className="mt-2 flex gap-1.5 overflow-x-auto">
          {photos.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectPhoto(w.id, p)}
              className={`spring h-12 w-16 flex-shrink-0 overflow-hidden rounded border-2 ${
                selectedId === p.id ? 'border-sun' : 'border-transparent hover:border-bubble'
              }`}
            >
              <img
                src={p.thumb_url}
                alt="Street photo"
                className="h-full w-full object-cover"
                loading="lazy"
              />
            </button>
          ))}
        </div>
      )}
      {photos && photos.length === 0 && (
        <p className="mt-1.5 text-xs text-white/40">No street photos nearby</p>
      )}
    </div>
  )
}
