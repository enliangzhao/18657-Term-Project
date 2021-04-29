var _ = require("underscore-node");

class People {
  constructor(index, health, pos, quarantine, vaccine, move, direction) {
    this.index = index;
    this.infect_date = 0;
    this.health = health;
    this.pos = pos;
    this.quarantine = quarantine;
    this.vaccine = vaccine;
    this.move = move;
    this.direction = direction;
  }
  print_person() {
    console.log(this.health);
  }
}

class city {
  constructor() {
    this.healthy = new Set();
    this.vaccinated = new Set();
    this.infected = new Set();
    this.death = new Set();
    // (x,y) : person
    this.graph = {};
    // this.num_iter = 0
    // (x,y) : //infected person
    this.matrix_length = 10;
    this.pop_size = 25;
    this.init_infected_rate = 0.2;
    this.infected_rate = 0;
    this.mobility = 0.5;
    // 1-e^(-lam*(x+1)) - (1-e^(-lam*x)
    this.death_rate = 0.1;
    this.recover_rate = 1 - this.death_rate;
    this.re_list = [];

    this.infected_period = 30;

    // 1-e^(-lam*(x+1)) - (1-e^(-lam*x)
    this.lam_death =
      (-1 * Math.log(1 - this.death_rate)) / this.infected_period;
    //  (1-e^(-lam)) - (1-e^(-lam*(x+1)) + (1-e^(-lam*x))
    this.lam_recover =
      (-1 * Math.log(1 - this.recover_rate)) / this.infected_period;

    this.num_iter = 550;
    this.K = 20;
    this.quarantine_rate = 0.5;
    // in each iteration, there will be this portion of healthy people get vaccinated
    this.vaccine_rate = 0.001;

    this.this_cure_rate = 0.001;
    this.Imax = 0;

    this.vaccine_release = 200;

    const directions = [
      (-1, -1),
      (-1, 0),
      (-1, 1),
      (0, -1),
      (0, 1),
      (1, -1),
      (1, 0),
      (1, 1),
    ];
    let tmp = [];
    for (let i = 0; i < this.matrix_length; i++) {
      for (let j = 0; j < this.matrix_length; j++) {
        tmp.push([i, j]);
      }
    }

    let random_init = _.sample(tmp, this.pop_size);
    let index = 0;

    random_init.array.forEach((element) => {
      let infected = Math.random();
      let quarantine = Math.random();
      let random_direction = _.sample(directions);
      let person = new People(
        index,
        infected < this.init_infected_rate ? 1 : 0,
        element,
        quarantine < this.quarantine_rate ? true : false,
        false,
        Math.random() < this.mobility ? true : false,
        random_direction,
      );

      if (person.health === 0) {
        this.healthy.add(person);
      } else {
        this.infected.add(person);
        // # this.graph_infected[x,y] += 1
      }
      this.graph[(x, y)] = person;
      index += 1;
    });
    this.re_list.push([this.infected.length]);
  }
  exponential(self, lam, x) {
    return 1 - Math.exp(-1 * lam * x);
  }

  has(set, target) {
    for (var x of set) {
      if (x[0] == target[0] && x[1] == target[1]) {
        return true;
      }
    }
    return false;
  }

  setDelete(set, target) {
    for (var x of set) {
      if (x[0] == target[0] && x[1] == target[1]) {
        set.delete(x);
      }
    }
  }

  arrayIndex(arr, subarr) {
    for (var i = 0; i < arr.length; i++) {
      let checker = false;
      for (var j = 0; j < arr[i].length; j++) {
        if (arr[i][j] === subarr[j]) {
          checker = true;
        } else {
          checker = false;
          break;
        }
      }
      if (checker) {
        return i;
      }
    }
    return -1;
  }

  iter() {
    const directions = [
      (-1, -1),
      (-1, 0),
      (-1, 1),
      (0, -1),
      (0, 1),
      (1, -1),
      (1, 0),
      (1, 1),
    ];
    this.re_list.push([this.infected.length]);
    let union_set = new Set(...this.healthy, ...this.infected); // to be fixed
    union_set.forEach((person) => {
      let x = person.pos[0];
      let y = person.pos[1];
      let dx = person.direction[0];
      let dy = person.direction[1];
      let nx = x + dx;
      let ny = y + dy;

      if (
        0 > nx &&
        nx >= this.matrix_length &&
        0 > ny &&
        ny >= this.matrix_length
      ) {
        directions.splice(this.arrayIndex(directions, [dx, dy]), 1);
        person.direction = _.sample(directions);
        directions.push([dx, dy]);
      } else if (this.has(this.graph, [nx, ny])) {
        let neighbor = this.graph[(nx, ny)];
        if (neighbor.health === 1) {
          if (person.health === 0) {
            this.setDelete(this.healthy, person);
            this.infected.add(person);
          }
          person.health = 1;
        } else if (person.health === 1) {
          if (neighbor.health === 0) {
            this.setDelete(this.healthy, neighbor);
            self.infected.add(neighbor);
          }
          neighbor.health = 1;
        }

        directions.splice(this.arrayIndex(directions, [dx, dy]), 1);
        person.direction = _.sample(directions);
        directions.push([dx, dy]);
      } else {
        person.pos = [nx, ny];
        this.setDelete(this.graph, [x, y]);
        this.graph[[nx, ny]] = person;
      }

      for (let item of this.infected) {
        item.infect_date += 1;
      }

      // +++++++++++++++++++++++++++++++++++++++++++
      for (let i = 0; i < this.matrix_length; i++) {
        for (let j = 0; j < this.matrix_length; j++) {
          if (this.has(this.graph, [i, j])) {
            break;
          }
          person = this.graph[[i, j]];

          if (
            person.health === 1 &&
            (person.infect_date === this.infected_period ||
              Math.random() <
                this.exponential(this.lam_recover, 0) -
                  this.exponential(this.lam_recover, person.infect_date + 1) +
                  this.exponential(this.lam_recover, person.infect_date))
          ) {
            person.health = 0;
            person.infect_date = 0;
            this.healthy.add(person);
            this.setDelete(this.infected, person);
          } else if (
            person.health === 1 &&
            Math.random() <
              this.exponential(this.lam_death, person.infect_date + 1) -
                this.exponential(this.lam_death, person.infect_date)
          ) {
            person.health = 2;
            this.death.add(person);
            this.setDelete(this.infected, person);
            this.setDelete(this.graph, [i, j]);
          }
        }
      }
    });
  }
}

let new_city = City();
num_iter = 10;

for (let i = 0; i < num_iter; i++) {
  if (new_city.healthy.length + new_city.infected.length === 0) {
    break;
  }
  console.log(i);
  new_city.iter();
}

Imax = max(new_city.re_list);
num_iter = len(new_city.re_list) - 1;

//let c = new city();
