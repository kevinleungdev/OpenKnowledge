import { Link } from '@tanstack/react-router'
import { LibraryBig } from 'lucide-react'
import { SidebarTrigger, useSidebar } from '@/components/ui/sidebar'

export function AppTitle() {
  const { setOpenMobile } = useSidebar()
  return (
    <div className='flex items-center gap-2'>
      {/* Branding - hidden when the sidebar collapses to the icon rail */}
      <Link
        to='/'
        onClick={() => setOpenMobile(false)}
        className='flex flex-1 items-center gap-2 rounded-md text-start text-sm leading-tight outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring group-data-[collapsible=icon]:hidden'
      >
        <span className='flex size-8 items-center justify-center rounded-md bg-sidebar-accent text-sidebar-accent-foreground'>
          <LibraryBig className='size-4' />
        </span>
        <span className='truncate font-semibold'>Open Knowledge</span>
      </Link>
      {/* Toggle - right-aligned (incl. collapsed icon rail and mobile sheet) */}
      <SidebarTrigger className='shrink-0 group-data-[collapsible=icon]:ms-auto' />
    </div>
  )
}
