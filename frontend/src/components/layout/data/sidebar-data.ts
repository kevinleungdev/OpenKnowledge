import {
  AudioWaveform,
  Bell,
  PlusSquare,
  Command,
  GalleryVerticalEnd,
  History,
  MessagesSquare,
  Monitor,
  Palette,
  Settings,
  SquareLibrary,
  UserCog,
  Wrench,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'Kevin Liang',
    email: 'kevinleungdev@gmail.com',
    avatar: '/avatars/shadcn.jpg',
  },
  teams: [
    {
      name: 'Open Knowledge',
      logo: Command,
      plan: 'Vite + ShadcnUI',
    },
    {
      name: 'Acme Inc',
      logo: GalleryVerticalEnd,
      plan: 'Enterprise',
    },
    {
      name: 'Acme Corp.',
      logo: AudioWaveform,
      plan: 'Startup',
    },
  ],
  navGroups: [
    {
      title: 'EXPLORE',
      items: [
        {
          title: 'Playground',
          url: '/playground',
          icon: MessagesSquare,
        },
        {
          title: 'History',
          url: '/users',
          icon: History,
        },
      ],
    },
    {
      title: 'KNOWLEDGE',
      items: [
        {
          title: 'Add Knowledge',
          url: '/users',
          icon: PlusSquare,
        },
        {
          title: 'Knowledge',
          url: '/apps',
          icon: SquareLibrary,
        },
      ],
    },
    {
      title: 'MANAGE',
      items: [
        {
          title: 'Settings',
          icon: Settings,
          items: [
            {
              title: 'Profile',
              url: '/settings',
              icon: UserCog,
            },
            {
              title: 'Account',
              url: '/settings/account',
              icon: Wrench,
            },
            {
              title: 'Appearance',
              url: '/settings/appearance',
              icon: Palette,
            },
            {
              title: 'Notifications',
              url: '/settings/notifications',
              icon: Bell,
            },
            {
              title: 'Display',
              url: '/settings/display',
              icon: Monitor,
            },
          ],
        },
      ],
    },
  ],
}
