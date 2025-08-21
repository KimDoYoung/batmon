function navData() {
    return {
        currentTime: '',
        init() {
            // 서버에서 시간을 가져오는 API 호출
            const url = "/api/v1/system/time";
            getFetch(url).then(data => {
                this.currentTime = data.time;
            });
            setInterval(() => {
                this.updateTime();
            }, 1000);
        },
        updateTime() {
            const now = new Date();
            const weekdays = ["월", "화", "수", "목", "금", "토", "일"];
            const weekdayStr = weekdays[now.getDay()];
            
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            
            this.currentTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds} (${weekdayStr})`;
        }
    };
}
