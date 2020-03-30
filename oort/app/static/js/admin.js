var admin = new Vue({
  el: '#admin',
  data: {
    admin: null,
    source: null
  },
  mounted: function () {
    const self = this
    this.source = new EventSource('/admin')
    this.source.onmessage = function (event) {
      const json = JSON.parse(event.data)
      console.log(json)
      self.admin = json.admin
      if (self.admin.close) {
        self.source.close()
        self.source.onmessage = null
        self.source = null
      }
    }
  }
})


