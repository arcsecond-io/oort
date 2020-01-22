var app = new Vue({
  el: '#app',
  data: {
    state: null,
    uploads: [],
    uploads_inactive: [],
    source: null
  },
  mounted: function () {
    const self = this
    this.source = new EventSource('/uploads')
    this.source.onmessage = function (event) {
      const json = JSON.parse(event.data)
      self.state = json.state
      self.uploads = json.uploads
      const bars = document.getElementsByClassName('progress-bar')
      self.uploads.forEach((upload, index) => {
        let bar = bars[index]
        if (bar) {
          bar.style.width = upload.progress.toFixed(1).toString() + '%'
        }
      })
    }
  }
})


