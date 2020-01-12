var app = new Vue({
  el: '#app',
  data: {
    message: 'Hello Vue!',
    uploads: [],
    source: null
  },
  mounted: function () {
    this.source = new EventSource('/uploads')
    const self = this
    this.source.onmessage = function (event) {
      self.uploads = JSON.parse(event.data)
    }
  }
})


