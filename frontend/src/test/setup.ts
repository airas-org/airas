import '@testing-library/jest-dom';
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// 各テストの後にクリーンアップ
afterEach(() => {
  cleanup();
});

