var header = new Vue({
  el: '#header',
  data: {
    state: null,
    source: null
  },
  mounted: function () {
    const self = this
    this.source = new EventSource('/header')
    this.source.onmessage = function (event) {
      const json = JSON.parse(event.data)
      console.log(json)
      self.state = json.state
    }
  }
})


