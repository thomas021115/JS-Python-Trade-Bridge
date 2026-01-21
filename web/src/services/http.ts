import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';


const apiClient: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
    headers: {
        'Content-Type': 'application/json', //未來可能會用 POST / PUT 傳資料給後端 先用content-type json
    },
    timeout: 10000, // 10 seconds timeout
});

apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
        return response.data;
    },
    (error) => {
        console.error('API Error:', error.response || error.message);
        return Promise.reject(error);
    }
);

export default apiClient;
