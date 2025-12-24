import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  PaperSearchExample,
  usePaperSearch,
  useBibfileGeneration,
  PaperSearchWithHook,
  PaperSearchWithErrorHandling,
} from './examples-react';
import { PapersService, BibfileService } from '../lib/api/index';
import type { RetrievePaperSubgraphResponseBody } from '../lib/api/index';
import type { GenerateBibfileSubgraphResponseBody } from '../lib/api/index';
import type { ResearchStudy } from '../lib/api/index';

// APIサービスのモック
vi.mock('../lib/api/index', () => ({
  PapersService: {
    getPaperTitleAirasV1PapersGet: vi.fn(),
  },
  BibfileService: {
    generateBibfileAirasV1BibfileGenerationsPost: vi.fn(),
  },
  OpenAPI: {
    BASE: '',
  },
}));

describe('examples-react.tsx', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 環境変数のモック
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('PaperSearchExample', () => {
    it('初期状態で正しくレンダリングされる', () => {
      render(<PaperSearchExample />);
      expect(screen.getByText('論文検索')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('検索クエリ 1')).toBeInTheDocument();
      expect(screen.getByText('+ クエリを追加')).toBeInTheDocument();
      expect(screen.getByText('検索')).toBeInTheDocument();
    });

    it('クエリ入力フィールドに値を入力できる', async () => {
      const user = userEvent.setup();
      render(<PaperSearchExample />);
      const input = screen.getByPlaceholderText('検索クエリ 1');
      await user.type(input, 'test query');
      expect(input).toHaveValue('test query');
    });

    it('クエリを追加できる', async () => {
      const user = userEvent.setup();
      render(<PaperSearchExample />);
      const addButton = screen.getByText('+ クエリを追加');
      await user.click(addButton);
      expect(screen.getByPlaceholderText('検索クエリ 1')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('検索クエリ 2')).toBeInTheDocument();
    });

    it('最大結果数を変更できる', async () => {
      const user = userEvent.setup();
      render(<PaperSearchExample />);
      const maxResultsInput = screen.getByLabelText('最大結果数:');
      await user.clear(maxResultsInput);
      await user.type(maxResultsInput, '20');
      expect(maxResultsInput).toHaveValue(20);
    });

    it('空のクエリでは検索ボタンが無効化される', () => {
      render(<PaperSearchExample />);
      const searchButton = screen.getByText('検索');
      expect(searchButton).toBeDisabled();
    });

    it('検索を実行して成功時に結果を表示する', async () => {
      const mockResearchStudy: ResearchStudy = {
        title: 'Test Paper',
        full_text: 'Test content',
        meta_data: {
          authors: ['Author 1'],
          year: 2024,
        } as any,
        llm_extracted_info: {} as any,
      };

      const mockResponse: RetrievePaperSubgraphResponseBody = {
        research_study_list: [[mockResearchStudy]],
        execution_time: {},
      };

      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockResolvedValue(
        mockResponse as any,
      );

      const user = userEvent.setup();
      render(<PaperSearchExample />);
      const input = screen.getByPlaceholderText('検索クエリ 1');
      await user.type(input, 'test');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText('検索結果:')).toBeInTheDocument();
      });

      expect(
        PapersService.getPaperTitleAirasV1PapersGet,
      ).toHaveBeenCalledWith({
        query_list: ['test'],
        max_results_per_query: 10,
      });
    });

    it('検索エラー時にエラーメッセージを表示する', async () => {
      const mockError = new Error('API Error');
      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockRejectedValue(
        mockError,
      );

      const user = userEvent.setup();
      render(<PaperSearchExample />);
      const input = screen.getByPlaceholderText('検索クエリ 1');
      await user.type(input, 'test');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText(/エラー:/)).toBeInTheDocument();
      });
    });

    it('空のクエリは検索リクエストから除外される', async () => {
      const mockResponse: RetrievePaperSubgraphResponseBody = {
        research_study_list: [],
        execution_time: {},
      };

      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockResolvedValue(
        mockResponse as any,
      );

      const user = userEvent.setup();
      render(<PaperSearchExample />);
      const addButton = screen.getByText('+ クエリを追加');
      await user.click(addButton);

      const input1 = screen.getByPlaceholderText('検索クエリ 1');
      await user.type(input1, 'query1');
      // input2は空のまま（追加されたが使用しない）

      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(
          PapersService.getPaperTitleAirasV1PapersGet,
        ).toHaveBeenCalledWith({
          query_list: ['query1'],
          max_results_per_query: 10,
        });
      });
    });
  });

  describe('usePaperSearch', () => {
    it('初期状態で正しい値を返す', () => {
      const TestComponent = () => {
        const { papers, loading, error } = usePaperSearch();
        return (
          <div>
            <div data-testid="papers">{papers ? 'has papers' : 'no papers'}</div>
            <div data-testid="loading">{loading ? 'loading' : 'not loading'}</div>
            <div data-testid="error">{error ? 'has error' : 'no error'}</div>
          </div>
        );
      };

      render(<TestComponent />);
      expect(screen.getByTestId('papers')).toHaveTextContent('no papers');
      expect(screen.getByTestId('loading')).toHaveTextContent('not loading');
      expect(screen.getByTestId('error')).toHaveTextContent('no error');
    });

    it('検索を実行して成功時に結果を返す', async () => {
      const mockResearchStudy: ResearchStudy = {
        title: 'Test',
        full_text: 'Test content',
        meta_data: {} as any,
        llm_extracted_info: {} as any,
      };

      const mockResponse: RetrievePaperSubgraphResponseBody = {
        research_study_list: [[mockResearchStudy]],
        execution_time: {},
      };

      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockResolvedValue(
        mockResponse as any,
      );

      const TestComponent = () => {
        const { papers, loading, error, searchPapers } = usePaperSearch();

        return (
          <div>
            <button onClick={() => searchPapers(['test'], 10)}>Search</button>
            <div data-testid="papers">{papers ? 'has papers' : 'no papers'}</div>
            <div data-testid="loading">{loading ? 'loading' : 'not loading'}</div>
            <div data-testid="error">{error ? 'has error' : 'no error'}</div>
          </div>
        );
      };

      const user = userEvent.setup();
      render(<TestComponent />);
      const searchButton = screen.getByText('Search');
      await user.click(searchButton);

      expect(screen.getByTestId('loading')).toHaveTextContent('loading');

      await waitFor(() => {
        expect(screen.getByTestId('papers')).toHaveTextContent('has papers');
      });

      expect(screen.getByTestId('loading')).toHaveTextContent('not loading');
      expect(screen.getByTestId('error')).toHaveTextContent('no error');
    });

    it('検索エラー時にエラーを返す', async () => {
      const mockError = new Error('API Error');
      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockRejectedValue(
        mockError,
      );

      const TestComponent = () => {
        const { papers, loading, error, searchPapers } = usePaperSearch();

        return (
          <div>
            <button
              onClick={() => {
                searchPapers(['test'], 10).catch(() => {
                  // エラーはフック内で処理される
                });
              }}
            >
              Search
            </button>
            <div data-testid="papers">{papers ? 'has papers' : 'no papers'}</div>
            <div data-testid="loading">{loading ? 'loading' : 'not loading'}</div>
            <div data-testid="error">{error ? error.message : 'no error'}</div>
          </div>
        );
      };

      const user = userEvent.setup();
      render(<TestComponent />);
      const searchButton = screen.getByText('Search');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('API Error');
      });

      expect(screen.getByTestId('loading')).toHaveTextContent('not loading');
    });
  });

  describe('useBibfileGeneration', () => {
    it('初期状態で正しい値を返す', () => {
      const TestComponent = () => {
        const { bibfile, loading, error } = useBibfileGeneration();
        return (
          <div>
            <div data-testid="bibfile">{bibfile ? 'has bibfile' : 'no bibfile'}</div>
            <div data-testid="loading">{loading ? 'loading' : 'not loading'}</div>
            <div data-testid="error">{error ? 'has error' : 'no error'}</div>
          </div>
        );
      };

      render(<TestComponent />);
      expect(screen.getByTestId('bibfile')).toHaveTextContent('no bibfile');
      expect(screen.getByTestId('loading')).toHaveTextContent('not loading');
      expect(screen.getByTestId('error')).toHaveTextContent('no error');
    });

    it('Bibfile生成を実行して成功時に結果を返す', async () => {
      const mockResponse: GenerateBibfileSubgraphResponseBody = {
        references_bib: '@article{test2024,\n  title={Test}\n}',
        execution_time: {},
      };

      vi.mocked(
        BibfileService.generateBibfileAirasV1BibfileGenerationsPost,
      ).mockResolvedValue(mockResponse as any);

      const TestComponent = () => {
        const { bibfile, loading, error, generateBibfile } =
          useBibfileGeneration();

        return (
          <div>
            <button
              onClick={() => generateBibfile([{ title: 'Test' }])}
            >
              Generate
            </button>
            <div data-testid="bibfile">
              {bibfile ? 'has bibfile' : 'no bibfile'}
            </div>
            <div data-testid="loading">{loading ? 'loading' : 'not loading'}</div>
            <div data-testid="error">{error ? 'has error' : 'no error'}</div>
          </div>
        );
      };

      const user = userEvent.setup();
      render(<TestComponent />);
      const generateButton = screen.getByText('Generate');
      await user.click(generateButton);

      expect(screen.getByTestId('loading')).toHaveTextContent('loading');

      await waitFor(() => {
        expect(screen.getByTestId('bibfile')).toHaveTextContent('has bibfile');
      });

      expect(screen.getByTestId('loading')).toHaveTextContent('not loading');
      expect(screen.getByTestId('error')).toHaveTextContent('no error');
    });

    it('Bibfile生成エラー時にエラーを返す', async () => {
      const mockError = new Error('Generation Error');
      vi.mocked(
        BibfileService.generateBibfileAirasV1BibfileGenerationsPost,
      ).mockRejectedValue(mockError);

      const TestComponent = () => {
        const { bibfile, loading, error, generateBibfile } =
          useBibfileGeneration();

        return (
          <div>
            <button
              onClick={() => {
                generateBibfile([{ title: 'Test' }]).catch(() => {
                  // エラーはフック内で処理される
                });
              }}
            >
              Generate
            </button>
            <div data-testid="bibfile">
              {bibfile ? 'has bibfile' : 'no bibfile'}
            </div>
            <div data-testid="loading">{loading ? 'loading' : 'not loading'}</div>
            <div data-testid="error">{error ? error.message : 'no error'}</div>
          </div>
        );
      };

      const user = userEvent.setup();
      render(<TestComponent />);
      const generateButton = screen.getByText('Generate');
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Generation Error');
      });

      expect(screen.getByTestId('loading')).toHaveTextContent('not loading');
    });
  });

  describe('PaperSearchWithHook', () => {
    it('初期状態で正しくレンダリングされる', () => {
      render(<PaperSearchWithHook />);
      expect(screen.getByText('論文検索（フック使用）')).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText('検索クエリを入力'),
      ).toBeInTheDocument();
      expect(screen.getByText('検索')).toBeInTheDocument();
    });

    it('クエリを入力して検索を実行できる', async () => {
      const mockResearchStudy: ResearchStudy = {
        title: 'Test',
        full_text: 'Test content',
        meta_data: {} as any,
        llm_extracted_info: {} as any,
      };

      const mockResponse: RetrievePaperSubgraphResponseBody = {
        research_study_list: [[mockResearchStudy]],
        execution_time: {},
      };

      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockResolvedValue(
        mockResponse as any,
      );

      const user = userEvent.setup();
      render(<PaperSearchWithHook />);
      const input = screen.getByPlaceholderText('検索クエリを入力');
      await user.type(input, 'test query');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText('検索結果:')).toBeInTheDocument();
      });
    });

    it('Enterキーで検索を実行できる', async () => {
      const mockResearchStudy: ResearchStudy = {
        title: 'Test',
        full_text: 'Test content',
        meta_data: {} as any,
        llm_extracted_info: {} as any,
      };

      const mockResponse: RetrievePaperSubgraphResponseBody = {
        research_study_list: [[mockResearchStudy]],
        execution_time: {},
      };

      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockResolvedValue(
        mockResponse as any,
      );

      const user = userEvent.setup();
      render(<PaperSearchWithHook />);
      const input = screen.getByPlaceholderText('検索クエリを入力');
      await user.type(input, 'test query{Enter}');

      await waitFor(() => {
        expect(screen.getByText('検索結果:')).toBeInTheDocument();
      });
    });

    it('空のクエリでは検索ボタンが無効化される', () => {
      render(<PaperSearchWithHook />);
      const searchButton = screen.getByText('検索');
      expect(searchButton).toBeDisabled();
    });
  });

  describe('PaperSearchWithErrorHandling', () => {
    it('初期状態で正しくレンダリングされる', () => {
      render(<PaperSearchWithErrorHandling />);
      expect(
        screen.getByText('論文検索（エラーハンドリング付き）'),
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText('検索クエリを入力'),
      ).toBeInTheDocument();
    });

    it('422エラー時に適切なエラーメッセージを表示する', async () => {
      const mockError: any = new Error('Validation Error');
      mockError.status = 422;
      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockRejectedValue(
        mockError,
      );

      const user = userEvent.setup();
      render(<PaperSearchWithErrorHandling />);
      const input = screen.getByPlaceholderText('検索クエリを入力');
      await user.type(input, 'test');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(
          screen.getByText('入力データが不正です。検索クエリを確認してください。'),
        ).toBeInTheDocument();
      });
    });

    it('404エラー時に適切なエラーメッセージを表示する', async () => {
      const mockError: any = new Error('Not Found');
      mockError.status = 404;
      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockRejectedValue(
        mockError,
      );

      const user = userEvent.setup();
      render(<PaperSearchWithErrorHandling />);
      const input = screen.getByPlaceholderText('検索クエリを入力');
      await user.type(input, 'test');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(
          screen.getByText('APIエンドポイントが見つかりません。'),
        ).toBeInTheDocument();
      });
    });

    it('500エラー時に適切なエラーメッセージを表示する', async () => {
      const mockError: any = new Error('Server Error');
      mockError.status = 500;
      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockRejectedValue(
        mockError,
      );

      const user = userEvent.setup();
      render(<PaperSearchWithErrorHandling />);
      const input = screen.getByPlaceholderText('検索クエリを入力');
      await user.type(input, 'test');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(
          screen.getByText(
            'サーバーエラーが発生しました。しばらくしてから再試行してください。',
          ),
        ).toBeInTheDocument();
      });
    });

    it('ステータスコードが表示される', async () => {
      const mockError: any = new Error('Server Error');
      mockError.status = 500;
      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockRejectedValue(
        mockError,
      );

      const user = userEvent.setup();
      render(<PaperSearchWithErrorHandling />);
      const input = screen.getByPlaceholderText('検索クエリを入力');
      await user.type(input, 'test');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText('ステータスコード: 500')).toBeInTheDocument();
      });
    });

    it('検索成功時に結果を表示する', async () => {
      const mockResearchStudy: ResearchStudy = {
        title: 'Test',
        full_text: 'Test content',
        meta_data: {} as any,
        llm_extracted_info: {} as any,
      };

      const mockResponse: RetrievePaperSubgraphResponseBody = {
        research_study_list: [[mockResearchStudy]],
        execution_time: {},
      };

      vi.mocked(PapersService.getPaperTitleAirasV1PapersGet).mockResolvedValue(
        mockResponse as any,
      );

      const user = userEvent.setup();
      render(<PaperSearchWithErrorHandling />);
      const input = screen.getByPlaceholderText('検索クエリを入力');
      await user.type(input, 'test');
      const searchButton = screen.getByText('検索');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText('検索結果:')).toBeInTheDocument();
      });
    });
  });
});

