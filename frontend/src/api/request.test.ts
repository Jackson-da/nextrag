/** request.ts 和批量上传 API 单元测试 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => {
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return {
    default: {
      create: vi.fn(() => mockInstance),
    },
  }
})

// Mock vue-router
vi.mock('@/router', () => ({ default: { push: vi.fn() } }))

// Mock element-plus
vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn() },
}))

// Re-import after mocks are set up
const { request } = await import('@/api/request')

// 获取 mock 后的 axios instance
const mockAxios = (axios.create as ReturnType<typeof vi.fn>).mock.results[0].value


describe('request.upload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should call instance.post with formData', async () => {
    const formData = new FormData()
    formData.append('files', new File(['test'], 'test.txt'))

    mockAxios.post.mockResolvedValue({ data: { success: true } })

    await request.upload('/documents/upload/batch', formData)

    expect(mockAxios.post).toHaveBeenCalledTimes(1)
    const [url, data] = mockAxios.post.mock.calls[0]
    expect(url).toBe('/documents/upload/batch')
    expect(data).toBe(formData)
  })

  it('should call instance.post with config options', async () => {
    const formData = new FormData()

    mockAxios.post.mockResolvedValue({ data: {} })

    await request.upload('/test/upload', formData, { timeout: 300000 })

    expect(mockAxios.post).toHaveBeenCalledTimes(1)
    const [, , config] = mockAxios.post.mock.calls[0]
    expect(config.timeout).toBe(300000)
  })
})





describe('Batch upload FormData construction', () => {
  it('should append multiple files correctly', () => {
    const formData = new FormData()
    const files = [
      new File(['content1'], 'doc1.txt', { type: 'text/plain' }),
      new File(['content2'], 'doc2.txt', { type: 'text/plain' }),
      new File(['content3'], 'doc3.txt', { type: 'text/plain' }),
    ]

    files.forEach((file) => {
      formData.append('files', file)
    })

    // FormData 的 getAll() 返回所有同名值
    const allFiles = formData.getAll('files')
    expect(allFiles).toHaveLength(3)
    expect((allFiles[0] as File).name).toBe('doc1.txt')
    expect((allFiles[1] as File).name).toBe('doc2.txt')
    expect((allFiles[2] as File).name).toBe('doc3.txt')
  })

  it('should include knowledge_base_id if provided', () => {
    const formData = new FormData()
    formData.append('files', new File(['test'], 'test.txt'))
    formData.append('knowledge_base_id', 'kb-123')

    expect(formData.get('knowledge_base_id')).toBe('kb-123')
  })

  it('should NOT include knowledge_base_id if not provided', () => {
    const formData = new FormData()
    formData.append('files', new File(['test'], 'test.txt'))

    expect(formData.get('knowledge_base_id')).toBeNull()
  })
})


describe('request base methods', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('request.get should call instance.get', async () => {
    mockAxios.get.mockResolvedValue({ data: [] })
    await request.get('/documents', { params: { skip: 0, limit: 20 } })
    expect(mockAxios.get).toHaveBeenCalledTimes(1)
  })

  it('request.post should call instance.post', async () => {
    mockAxios.post.mockResolvedValue({ data: { id: '1' } })
    await request.post('/knowledge-bases', { name: 'test' })
    expect(mockAxios.post).toHaveBeenCalledTimes(1)
  })

  it('request.put should call instance.put', async () => {
    mockAxios.put.mockResolvedValue({ data: { id: '1' } })
    await request.put('/knowledge-bases/1', { name: 'updated' })
    expect(mockAxios.put).toHaveBeenCalledTimes(1)
  })

  it('request.delete should call instance.delete', async () => {
    mockAxios.delete.mockResolvedValue({ data: { success: true } })
    await request.delete('/documents/1')
    expect(mockAxios.delete).toHaveBeenCalledTimes(1)
  })
})
