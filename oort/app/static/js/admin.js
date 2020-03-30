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
      self.context = json.context
    }
  }
})


