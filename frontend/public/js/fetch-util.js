
/**
 * fetch API 호출시 server로 부터 받은 response가 에러인 경우 
 * status와 detail을 저장하는 Error클래스
 */
class BatmonError extends Error {
    constructor(status, detail, server_time) {
        super(detail);
        this.status = status;
        this.server_time = server_time;
    }
    toString() {
        return `Error ${this.status}: ${this.message} (Server Time: ${this.server_time})`;
    }    
}
/**
 * 공통 fetch 함수
 * 
 * @param {string} url - 요청할 URL
 * @param {string} method - HTTP 메서드 ('GET', 'POST', 'PUT', 'DELETE')
 * @param {Object} [data] - 요청에 포함할 데이터 (옵션)
 * @returns {Promise<Object>} - 응답 데이터
 */
async function callApi(url, method, data = null) {
    // const token = localStorage.getItem('kiwi_token');

    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                // 'Authorization': 'Bearer ' + token
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }
        const response = await fetch(url, options);
        
        // 세션 타임아웃으로 인해 401 상태 코드가 반환되었는지 체크
        if (response.status === 401) {
            console.error('세션이 만료되었습니다.');
            // 사용자에게 로그인 페이지로 리다이렉트하도록 처리
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            console.error('에러 발생:', response);
            // 응답이 JSON인지 체크하여 에러 데이터 처리
            const contentType = response.headers.get('content-type');            
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                // 에러 형식에 맞게 수정
                const errorMessage = errorData.error_message || errorData.detail || 'Unknown error';
                throw new BatmonError(response.status, errorMessage, response.response_time);
            } else {
                throw new BatmonError(response.status, 'Unexpected response format', response.response_time);
            }            
        }

        const responseData = await response.json();
        return responseData;
    } catch (error) {
        let errorStr = error.toString();
        if (errorStr.includes('SyntaxError: Unexpected end of JSON input')) {
            alert("세션 종료되었습니다. 서버와의 통신이 원활하지 않습니다. 다시 로그인해주세요.");
            window.location.href = '/login';
        } else {
            throw new BatmonError(500, errorStr);
        }
    }
}

/**
 * GET 요청 함수
 * 
 * @param {string} url - 요청할 URL
 * @returns {Promise<Object>} - 응답 데이터
 */
async function getFetch(url) {
    return callApi(url, 'GET');
}

/**
 * POST 요청 함수
 * 
 * @param {string} url - 요청할 URL
 * @param {Object} data - 요청에 포함할 데이터
 * @returns {Promise<Object>} - 응답 데이터
 */
async function postFetch(url, data) {
    return callApi(url, 'POST', data);
}

/**
 * PUT 요청 함수
 * 
 * @param {string} url - 요청할 URL
 * @param {Object} data - 요청에 포함할 데이터
 * @returns {Promise<Object>} - 응답 데이터
 */
async function putFetch(url, data) {
    return callApi(url, 'PUT', data);
}

/**
 * DELETE 요청 함수
 * 
 * @param {string} url - 요청할 URL
 * @param {Object} data - 요청에 포함할 데이터
 * @returns {Promise<Object>} - 응답 데이터
 */
async function deleteFetch(url, data) {
    return callApi(url, 'DELETE', data);
}

