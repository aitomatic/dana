# DXA Dana UI

A modern React-based user interface for managing Domain-Expert Agents (DXA) with a comprehensive library system and agent creation capabilities.

## 🚀 Features

- **Agent Management**: Create, view, and manage Domain-Expert Agents
- **Library System**: File and folder management with drag-and-drop support
- **Modern UI**: Built with Tailwind CSS and Radix UI components
- **Code Editor**: Monaco Editor integration for agent code editing
- **Responsive Design**: Mobile-friendly interface with collapsible sidebar
- **Type Safety**: Full TypeScript support throughout the application

## 🛠️ Tech Stack

- **Frontend Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4
- **UI Components**: Radix UI + Custom components
- **Icons**: Iconoir React + Tabler Icons
- **State Management**: Zustand
- **Routing**: React Router DOM
- **Code Editor**: Monaco Editor
- **Forms**: React Hook Form
- **Tables**: TanStack React Table

## 📦 Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd dxa-dana-ui
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## 🏗️ Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── agent-editor/   # Agent creation/editing components
│   ├── library/        # Library management components
│   ├── table/          # Data table components
│   └── ui/             # Base UI components (buttons, inputs, etc.)
├── hooks/              # Custom React hooks
├── pages/              # Page components
│   ├── Agents/         # Agent management pages
│   └── Library/        # Library pages
├── stores/             # Zustand state stores
├── types/              # TypeScript type definitions
└── lib/                # Utility functions
```

## 🎨 UI Components

The application uses a mix of icon libraries:

- **Iconoir React**: Main navigation items (Domain-Expert Agents uses Tray3d icon, Library uses Book icon)
- **Tabler Icons**: Other UI elements throughout the application

## 🔧 Development

### Code Style

- ESLint configuration with TypeScript support
- Prettier for code formatting
- Strict TypeScript configuration

### Component Guidelines

- Use TypeScript for all components
- Follow the established component structure
- Use Tailwind CSS for styling
- Implement responsive design patterns

### State Management

- Use Zustand for global state management
- Local component state with React hooks
- Form state managed with React Hook Form

## 🚀 Deployment

Build the application for production:

```bash
npm run build
```

The built files will be in the `dist` directory, ready for deployment to your hosting platform.

## 📝 License

This project is private and proprietary.

## 🤝 Contributing

1. Follow the established code style and patterns
2. Ensure all TypeScript types are properly defined
3. Test your changes thoroughly
4. Update documentation as needed

---

For more information about Domain-Expert Agents and the Dana platform, please refer to the project documentation.
