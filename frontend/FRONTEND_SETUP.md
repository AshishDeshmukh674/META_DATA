# 🚀 Frontend Setup & Launch Guide

Complete step-by-step guide to get the Lakehouse Explorer frontend up and running.

## ✅ Prerequisites Checklist

Before starting, ensure you have:

- [ ] Node.js 18 or higher installed
- [ ] npm (comes with Node.js)
- [ ] Backend API running on port 8001
- [ ] Trino running on port 8080 (Docker)
- [ ] Git (for version control)

### Check Node.js Version

```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 8.0.0 or higher
```

If Node.js is not installed, download from: https://nodejs.org/

## 📦 Step 1: Install Dependencies

Open PowerShell and navigate to the frontend directory:

```powershell
cd C:\Users\ashis\Desktop\META\frontend
```

Install all required packages:

```powershell
npm install
```

This will install:
- Next.js 14
- React 18
- TypeScript
- TailwindCSS
- Axios
- Lucide Icons
- React Hot Toast
- And all other dependencies

**Expected Output**:
```
added 300+ packages in 30s
```

## ⚙️ Step 2: Configure Environment

The `.env.local` file is already configured with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**If your backend runs on a different port**, edit `.env.local`:

```powershell
notepad .env.local
```

Change the URL accordingly.

## 🎯 Step 3: Start the Development Server

Run the development server:

```powershell
npm run dev
```

**Expected Output**:
```
  ▲ Next.js 14.1.0
  - Local:        http://localhost:3000
  - Ready in 2.5s
```

## 🌐 Step 4: Open in Browser

Open your browser and navigate to:

**http://localhost:3000**

You should see the Lakehouse Explorer homepage with:
- ✅ Navigation bar at the top
- ✅ Hero section with gradient title
- ✅ API status indicator
- ✅ Four feature cards
- ✅ Benefits section

## 🧪 Step 5: Test the Application

### Test 1: Check API Connection

1. Look at the homepage - you should see "API Status: Connected" (green dot)
2. If it shows "Offline", check that your backend is running on port 8001

### Test 2: Natural Language Query

1. Click **"Natural Language Query"** in the navigation or the feature card
2. You should see:
   - Example questions at the top
   - A form with query input
   - Table configuration fields
   - Tips and guide on the right

3. Click "Sync Table" to register your table schema
4. Click an example query like "Show me all customers from Mumbai"
5. Click "Ask Question"
6. You should see:
   - Generated SQL query
   - Query results in a table
   - Execution time

### Test 3: SQL Query Editor

1. Navigate to **SQL Query**
2. Click an example query to load it
3. Click "Execute Query" or press Ctrl+Enter
4. Verify results appear in the table below

### Test 4: Metadata Generation

1. Navigate to **Metadata**
2. The default CSV path should be pre-filled
3. Click "Generate Metadata"
4. Wait for conversion (1-2 seconds)
5. Verify success message and schema display

### Test 5: Snapshots

1. Navigate to **Snapshots**
2. Click "Load Snapshots"
3. Verify snapshot list appears
4. Click "Query" on any snapshot
5. Verify data is displayed

### Test 6: Settings

1. Navigate to **Settings**
2. Click "Test Connection"
3. Verify "Connected" status appears
4. Try changing default settings
5. Click "Save Settings"

## 🎨 Feature Walkthrough

### Navigation Bar
- **Logo**: Click to return home
- **Home**: Main landing page
- **Natural Language**: AI-powered queries
- **SQL Query**: Direct SQL editor
- **Metadata**: CSV to Delta conversion
- **Snapshots**: Time travel queries
- **Settings**: Configuration

### UI Components

**Buttons**:
- Primary (blue) - Main actions
- Outline - Secondary actions
- Ghost - Minimal actions

**Alerts**:
- 🔴 Red - Errors
- 🟢 Green - Success
- 🟡 Yellow - Warnings
- 🔵 Blue - Information

**Tables**:
- Scrollable results
- Row count and execution time
- Null value handling
- Responsive design

**Code Blocks**:
- Syntax highlighting
- Copy to clipboard button
- Language labels

## 🔧 Troubleshooting

### Issue: Port 3000 Already in Use

**Error**: `Port 3000 is already in use`

**Solution**:
```powershell
# Find the process
netstat -ano | findstr :3000

# Kill the process (replace <PID> with actual PID)
taskkill /PID <PID> /F

# Or use a different port
npm run dev -- -p 3001
```

### Issue: API Connection Failed

**Symptoms**: "API Status: Offline" on homepage

**Solutions**:

1. **Check backend is running**:
```powershell
# Open new PowerShell window
cd C:\Users\ashis\Desktop\META
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

2. **Check backend URL**:
- Open `.env.local`
- Verify: `NEXT_PUBLIC_API_URL=http://localhost:8001`

3. **Test backend directly**:
- Open browser to http://localhost:8001/docs
- Should see FastAPI Swagger UI

4. **Check CORS settings** in backend

### Issue: Module Not Found

**Error**: `Cannot find module 'xyz'`

**Solution**:
```powershell
# Reinstall dependencies
rm -r node_modules
rm package-lock.json
npm install
```

### Issue: TypeScript Errors

**Error**: Type errors in console

**Solution**:
```powershell
# Check TypeScript compilation
npm run build

# If errors persist, check tsconfig.json
```

### Issue: Styles Not Loading

**Symptoms**: Page appears unstyled

**Solution**:
```powershell
# Clear Next.js cache
rm -r .next
npm run dev
```

### Issue: Hot Reload Not Working

**Solution**:
```powershell
# Stop the server (Ctrl+C)
# Clear cache
rm -r .next
# Restart
npm run dev
```

## 🏗️ Production Build

To build for production:

```powershell
# Build optimized bundle
npm run build

# Start production server
npm start
```

The production server will run on http://localhost:3000

## 📊 Full Stack Launch Sequence

**Complete startup order for the entire application**:

### Terminal 1: Start Trino (Docker)
```powershell
docker start trino
# Wait for: Container trino started
```

### Terminal 2: Start Backend API
```powershell
cd C:\Users\ashis\Desktop\META
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
# Wait for: Uvicorn running on http://127.0.0.1:8001
```

### Terminal 3: Start Frontend
```powershell
cd C:\Users\ashis\Desktop\META\frontend
npm run dev
# Wait for: Ready in 2.5s
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Trino UI**: http://localhost:8080

## 🎯 Development Tips

### Hot Reload
- Changes to files in `src/` auto-reload
- No need to restart the server
- Check terminal for compilation errors

### Console Logging
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for API calls

### Component Development
- Edit components in `src/components/`
- Changes reflect immediately
- Follow existing patterns

### API Integration
- All API functions in `src/lib/api/queries.ts`
- TypeScript types in `src/lib/types/api.ts`
- Axios client in `src/lib/api/client.ts`

### Styling
- Use TailwindCSS utility classes
- Custom styles in `src/app/globals.css`
- Theme tokens in `tailwind.config.ts`

## 📱 Testing Responsive Design

**Desktop** (default):
- Open http://localhost:3000
- Full features visible

**Tablet** (768px):
- Open DevTools (F12)
- Click "Toggle device toolbar"
- Select "iPad"
- Verify layout adjusts

**Mobile** (375px):
- Select "iPhone SE"
- Verify navigation collapses
- Verify tables scroll horizontally
- Verify cards stack vertically

## 🔐 Security Notes

- Never commit `.env.local` to Git
- API keys should be server-side only
- Frontend calls backend, backend calls external APIs
- Groq API key stays in backend `.env`

## ✨ What You Have Now

A complete, production-ready frontend with:

✅ **6 fully functional pages**
✅ **10+ reusable UI components**
✅ **TypeScript type safety**
✅ **Responsive design (mobile, tablet, desktop)**
✅ **Modern UI with TailwindCSS**
✅ **Toast notifications**
✅ **Loading states**
✅ **Error handling**
✅ **Copy to clipboard**
✅ **Example queries**
✅ **Form validation**
✅ **API integration**
✅ **Settings persistence**
✅ **Dark mode ready**

## 🎉 Next Steps

1. **Customize**: Edit colors, fonts, spacing in `tailwind.config.ts`
2. **Add Features**: Create new pages in `src/app/`
3. **Enhance Components**: Extend UI components in `src/components/ui/`
4. **Add Analytics**: Integrate tracking (Google Analytics, etc.)
5. **Deploy**: Deploy to Vercel, Netlify, or other hosting

## 📖 Learning Resources

- **Next.js Docs**: https://nextjs.org/docs
- **React Docs**: https://react.dev
- **TailwindCSS**: https://tailwindcss.com/docs
- **TypeScript**: https://www.typescriptlang.org/docs

## 🆘 Getting Help

If you encounter issues:

1. Check browser console (F12) for errors
2. Check terminal output for build errors
3. Verify all services are running
4. Check network tab for failed API calls
5. Review this guide and README.md

---

**Congratulations! 🎊**

Your Lakehouse Explorer frontend is now running. Enjoy exploring your data with natural language and SQL queries!
