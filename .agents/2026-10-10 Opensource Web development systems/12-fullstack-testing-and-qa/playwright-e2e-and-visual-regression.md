# Playwright E2E & Visual Regression Testing Guide (2026)

> Production testing guide for end-to-end browser automation, CI execution matrices, and visual regression detection.

---

## 1. Playwright Test Architecture

Playwright provides cross-browser automation across Chromium, WebKit, and Firefox with native support for parallel worker execution, trace recordings, and video captures.

### 1.1 `playwright.config.ts` Configuration

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [['html'], ['list']],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 14'] },
    },
  ],
  webServer: {
    command: 'npm run start',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 2. Authentication State Reuse (Storage State)

Avoid repeating full login UI flows for every test by authenticating once and saving browser state:

```ts
// e2e/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate user', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill('SuperSecret123!');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await page.waitForURL('/dashboard');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

  await page.context().storageState({ path: authFile });
});
```

Tests consume the cached session:
```ts
// e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.use({ storageState: 'playwright/.auth/user.json' });

test('displays active projects with zero login delay', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page.getByText('Active Projects')).toBeVisible();
});
```

---

## 3. Visual Regression Snapshots

Catch accidental CSS layout breakage across pull requests:

```ts
test('landing page visually matches golden snapshot', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Compare viewport screenshot against baseline image with 1% max difference threshold
  await expect(page).toHaveScreenshot('landing-page.png', {
    maxDiffPixelRatio: 0.01,
  });
});
```
