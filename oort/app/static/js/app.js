var app = new Vue({
  el: '#app',
  data: {
    uploads_active: [],
    uploads_inactive: [],
    source_active: null,
    source_inactive: null
  },
  mounted: function () {
    const self = this
    this.source_active = new EventSource('/uploads/active')
    this.source_active.onmessage = function (event) {
      self.uploads_active = JSON.parse(event.data)
      const bars = document.getElementsByClassName('progress-bar')
      self.uploads_active.forEach((upload, index) => {
        let bar = bars[index]
        if (bar) {
          bar.style.width = upload.progress.toFixed(1).toString() + '%'
        }
      })
    }
    this.source_inactive = new EventSource('/uploads/inactive')
    this.source_inactive.onmessage = function (event) {
      self.uploads_inactive = JSON.parse(event.data)
    }
  }
})


