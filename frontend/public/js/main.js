function dashboard() {
    return {
      dmst_stex_tp: 'KRX',
      stk_cd: '',
      ord_qty: '1',
      ord_uv: '',
      trde_tp: '3',
      cond_uv: '',
      result: '',
      error: '',

      async submit() {
        this.result = '';
        this.error = '';
        try {
          const payload = {
            dmst_stex_tp: this.dmst_stex_tp,
            stk_cd: this.stk_cd,
            ord_qty: this.ord_qty,
            ord_uv: this.ord_uv || null,
            trde_tp: this.trde_tp,
            cond_uv: this.cond_uv || null,
          };

          // fetch-util.js의 callKiwoomApi 함수 사용
          const response = await callKiwoomApi('kt10000', payload);

          if (response.success) {
            this.result = response.data.return_msg || '주문이 성공적으로 처리되었습니다.';
            console.log('주문 응답:', response.data);
          } else {
            throw new Error(response.error_message || '알 수 없는 오류가 발생했습니다.');
          }
        } catch (err) {
          if (err instanceof KiwiError) {
            this.error = `에러 ${err.status}: ${err.message}`;
          } else {
            this.error = '에러: ' + err.message;
          }
          console.error('주문 처리 오류:', err);
        }
      }
    };
  }