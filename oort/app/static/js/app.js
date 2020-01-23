var app = new Vue({
  el: '#app',
  data: {
    state: null,
    uploads: [],
    finished_uploads: [],
    source: null
  },
  mounted: function () {
    const self = this
    this.source = new EventSource('/uploads')
    this.source.onmessage = function (event) {
      const json = JSON.parse(event.data)
      self.state = json.state
      self.uploads = json.uploads.sort((u1, u2) => new Date(u1.started).getDate() < new Date(u2.started).getDate())
      self.finished_uploads = json.finished_uploads.sort((u1, u2) => new Date(u1.ended).getDate() < new Date(u2.ended).getDate())
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


