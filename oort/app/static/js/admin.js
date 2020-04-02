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
      self.admin = json.admin
      if (self.admin['night_log']) {
        self.admin['night_log_url'] = 'data/' + self.admin['night_log']['date'].replace(/-/gi, '/')
      }
      if (self.admin.close) {
        self.source.close()
        self.source.onmessage = null
        self.source = null
      }
    }
  }
})


