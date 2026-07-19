import {
  Bell,
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
      title: 'BUILD',
      items: [
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
