# Lakehouse Explorer - Frontend

Modern, responsive Next.js frontend for the Lakehouse Explorer application. Query your Delta Lake data using natural language or SQL with a beautiful, intuitive interface.

## 🎨 Features

- **Natural Language Queries** - Ask questions in plain English, AI converts to SQL
- **SQL Query Editor** - Write and execute SQL directly with syntax highlighting
- **Metadata Generation** - Convert CSV files to Delta Lake format
- **Time Travel** - Query historical snapshots of your data
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Dark Mode Ready** - Beautiful UI with theme support
- **Real-time Updates** - Toast notifications and loading states
- **Copy to Clipboard** - Easy copying of queries and results

## 🚀 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Notifications**: React Hot Toast

## 📋 Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8001
- Trino running on port 8080 (Docker)

## 🛠️ Installation

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure environment** (optional):
Edit `.env.local` to change the API URL:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

4. **Run development server**:
```bash
npm run dev
```

5. **Open in browser**:
Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router pages
│   │   ├── layout.tsx          # Root layout with providers
│   │   ├── page.tsx            # Homepage
│   │   ├── natural-language/   # Natural language query page
│   │   ├── sql-query/          # SQL editor page
│   │   ├── metadata/           # Metadata generation page
│   │   ├── snapshots/          # Time travel page
│   │   └── settings/           # Settings page
│   ├── components/
│   │   ├── ui/                 # Reusable UI components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── loading.tsx
│   │   │   └── alert.tsx
│   │   ├── data-table.tsx      # Data display component
│   │   ├── code-block.tsx      # Code viewer with copy
│   │   └── navigation.tsx      # Top navigation bar
│   └── lib/
│       ├── api/
│       │   ├── client.ts       # Axios client setup
│       │   └── queries.ts      # API functions
│       ├── types/
│       │   └── api.ts          # TypeScript types
│       └── utils.ts            # Utility functions
├── public/                     # Static assets
├── .env.local                  # Environment variables
├── next.config.js              # Next.js configuration
├── tailwind.config.ts          # TailwindCSS configuration
├── tsconfig.json               # TypeScript configuration
└── package.json                # Dependencies
```

## 🎯 Pages

### 1. Home (`/`)
- Overview of features
- Quick start guide
- API status indicator
- Feature cards with navigation

### 2. Natural Language Query (`/natural-language`)
- Text input for questions in plain English
- Example queries
- Table configuration (storage type, bucket, path)
- Table sync button
- Generated SQL display
- Query results table
- Tips and how-it-works guide

### 3. SQL Query Editor (`/sql-query`)
- SQL textarea with syntax highlighting
- Example queries library
- Execute button (Ctrl+Enter shortcut)
- Connection test
- Query results display
- Fast execution with Trino

### 4. Metadata Generation (`/metadata`)
- CSV file path input
- Storage configuration
- Force refresh option
- Schema detection and display
- Snapshot information
- Conversion process guide

### 5. Snapshots & Time Travel (`/snapshots`)
- List available snapshots
- Query specific versions
- Snapshot metadata display
- Time travel SQL syntax
- Historical data comparison

### 6. Settings (`/settings`)
- API connection configuration
- Default table settings
- Theme selection
- Connection testing
- System information

## 🔧 Configuration

### API Configuration

Edit `src/lib/api/client.ts` to customize:
- Base URL
- Timeout duration
- Request/response interceptors
- Error handling

### Styling

Edit `tailwind.config.ts` to customize:
- Colors
- Spacing
- Typography
- Animations

### Environment Variables

`.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 🎨 UI Components

### Button Variants
- `default` - Primary action
- `destructive` - Delete/dangerous actions
- `outline` - Secondary action
- `secondary` - Low emphasis
- `ghost` - Minimal style
- `link` - Text link style

### Alert Variants
- `default` - General information
- `destructive` - Errors
- `success` - Success messages
- `warning` - Warnings
- `info` - Helpful information

### Loading States
- `LoadingSpinner` - Small spinner
- `LoadingOverlay` - Full screen
- `LoadingCard` - Inline card loader

## 📡 API Integration

All API calls are in `src/lib/api/queries.ts`:

```typescript
// Natural language query
await executeNaturalLanguageQuery({
  natural_language_query: "Show all customers",
  storage_type: "local",
  table_path: "path/to/table"
});

// SQL query
await executeSQL({
  sql_query: "SELECT * FROM delta.default.customers"
});

// Generate metadata
await generateMetadata({
  csv_path: "data/customers.csv",
  storage_type: "local",
  force_refresh: false
});

// List snapshots
await listSnapshots({
  storage_type: "local",
  table_path: "path/to/table"
});

// Sync table
await syncTable({
  storage_type: "local",
  table_path: "path/to/table"
});

// Check health
await checkHealth();
```

## 🚦 Running the Full Stack

1. **Start Trino (Docker)**:
```bash
docker start trino
```

2. **Start Backend API**:
```bash
cd ..
.venv\Scripts\activate  # Windows
uvicorn app.main:app --reload --port 8001
```

3. **Start Frontend**:
```bash
cd frontend
npm run dev
```

4. **Access Application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Trino: http://localhost:8080

## 📦 Build for Production

```bash
# Build optimized production bundle
npm run build

# Start production server
npm start
```

The build output will be in `.next/` directory.

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### API Connection Failed
- Ensure backend is running on port 8001
- Check `.env.local` has correct API URL
- Verify CORS is enabled on backend
- Check network/firewall settings

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors
```bash
# Check types
npm run type-check

# Generate types
npm run build
```

## 🎯 Best Practices

### Component Structure
- Keep components small and focused
- Use TypeScript interfaces for props
- Extract reusable logic to hooks
- Follow Next.js 14 App Router conventions

### State Management
- Use local state for UI state
- Use API queries for server state
- Minimize global state
- Leverage React Server Components when possible

### Performance
- Use `use client` only when needed
- Optimize images with Next.js Image component
- Lazy load heavy components
- Minimize bundle size

### Styling
- Use TailwindCSS utility classes
- Follow design system tokens
- Maintain consistent spacing
- Ensure responsive design

## 🔐 Security

- API URL is configurable via environment variables
- No sensitive data in frontend code
- HTTPS recommended for production
- Validate all user inputs
- Sanitize displayed data

## 📱 Responsive Design

Breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

Mobile-first approach with responsive utilities.

## 🌐 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 📄 License

This project is part of the META Lakehouse Explorer platform.

## 🤝 Contributing

1. Follow the existing code style
2. Write meaningful commit messages
3. Test on multiple screen sizes
4. Update documentation as needed

## 📞 Support

For issues or questions:
- Check the main README.md
- Review API documentation at `/docs`
- Check browser console for errors
- Verify backend is running correctly

---

Built with ❤️ using Next.js 14 and TailwindCSS
